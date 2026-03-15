import os
import json
import logging
import base64
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from backend.core.permissions import enforce_permission, set_chip_context
from .models import SyncPackage, SyncAction, SyncStatus, DeviceInfo

logger = logging.getLogger(__name__)

class SyncManager:
    """
    Asset & Workspace Sync Engine for OmniWeb.
    Phase 21: Distributed Node Sync.
    """

    def __init__(self, workspace_root: str = "user_workspace"):
        self.workspace_root = workspace_root

    def register_device(self, user_id: str, device_id: str, device_name: str, metadata: Dict[str, Any] = {}) -> bool:
        """Registers a device for a user."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sync_devices (device_id, user_id, device_name, metadata, last_sync)
                    VALUES (?, ?, ?, ?, ?)
                """, (device_id, user_id, device_name, json.dumps(metadata), datetime.now()))
                conn.commit()
        return True

    def get_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Lists all registered devices for a user."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM sync_devices WHERE user_id = ?", (user_id,)).fetchall()
                return [dict(r) for r in rows]

    def prepare_package(self, user_id: str, last_sync_time: Optional[datetime] = None) -> SyncPackage:
        """Collects changes since last_sync_time."""
        # Note: In a real implementation, we would query by updated_at > last_sync_time.
        # Here we collect relevant records to demonstrate the model.
        
        logbook_entries = []
        graph_nodes = []
        graph_edges = []
        tombstones = []
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Logbook
                query = "SELECT * FROM user_logbooks WHERE user_id = ?"
                params = [user_id]
                if last_sync_time:
                    query += " AND timestamp > ?"
                    params.append(last_sync_time)
                
                rows = conn.execute(query, params).fetchall()
                logbook_entries = [dict(r) for r in rows]

                # 2. Graph Nodes
                query = "SELECT * FROM user_graph_nodes WHERE user_id = ?"
                params = [user_id]
                if last_sync_time:
                    query += " AND timestamp > ?"
                    params.append(last_sync_time)
                
                rows = conn.execute(query, params).fetchall()
                graph_nodes = [dict(r) for r in rows]

                # 3. Tombstones
                query = "SELECT * FROM sync_tombstones WHERE user_id = ?"
                params = [user_id]
                if last_sync_time:
                    query += " AND deleted_at > ?"
                    params.append(last_sync_time)
                rows = conn.execute(query, params).fetchall()
                tombstones = [dict(r) for r in rows]

        # 4. Workspace Assets (Simplified fingerprinting)
        workspace_files = []
        user_path = os.path.join(self.workspace_root, user_id)
        if os.path.exists(user_path):
            for root, dirs, files in os.walk(user_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, user_path)
                    
                    # Skip potentially huge or binary files for this demo to prevent payload explosion
                    # In production this would be handled via block sync or chunked uploads
                    if file.endswith(('.json', '.txt', '.md', '.log')):
                        try:
                            mtime = os.path.getmtime(full_path)
                            if not last_sync_time or mtime > last_sync_time.timestamp():
                                with open(full_path, "rb") as f:
                                    content = f.read()
                                    content_b64 = base64.b64encode(content).decode('utf-8')
                                    file_hash = hashlib.sha256(content).hexdigest()
                                    workspace_files.append({
                                        "path": rel_path,
                                        "content": content_b64,
                                        "hash": file_hash,
                                        "modified_at": mtime
                                    })
                        except Exception as e:
                            logger.error(f"Failed to process file for sync: {rel_path} - {e}")

        return SyncPackage(
            device_id="local", # Should be replaced by caller
            user_id=user_id,
            timestamp=datetime.now().timestamp(),
            logbook_entries=logbook_entries,
            graph_nodes=graph_nodes,
            tombstones=tombstones,
            workspace_files=workspace_files
        )

    def ingest_package(self, package: SyncPackage) -> Dict[str, Any]:
        """Applies a sync package from another device."""
        results = {"applied": 0, "conflicts": 0, "skipped": 0}
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Apply Logbook Entries (Last Write Wins)
                for entry in package.logbook_entries:
                    # Check existing
                    existing = conn.execute("SELECT timestamp FROM user_logbooks WHERE id = ?", (entry["id"],)).fetchone()
                    if not existing or entry["timestamp"] > existing["timestamp"]:
                        conn.execute("""
                            INSERT OR REPLACE INTO user_logbooks (id, user_id, entry_type, content, timestamp, metadata)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (entry["id"], entry["user_id"], entry["entry_type"], entry["content"], entry["timestamp"], entry["metadata"]))
                        results["applied"] += 1
                    else:
                        results["skipped"] += 1

                # 2. Process Tombstones
                for ts in package.tombstones:
                    if ts["target_type"] == "logbook":
                        conn.execute("DELETE FROM user_logbooks WHERE id = ? AND user_id = ?", (ts["original_id"], package.user_id))
                    elif ts["target_type"] == "graph":
                        conn.execute("DELETE FROM user_graph_nodes WHERE id = ? AND user_id = ?", (ts["original_id"], package.user_id))
                    results["applied"] += 1

                # 3. Workspace Files (Filesystem Sync)
                user_path = os.path.join(self.workspace_root, package.user_id)
                os.makedirs(user_path, exist_ok=True)
                
                for f_info in package.workspace_files:
                    target_file = os.path.join(user_path, f_info["path"])
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    
                    # Conflict check
                    should_write = True
                    if os.path.exists(target_file):
                        local_mtime = os.path.getmtime(target_file)
                        if local_mtime > f_info["modified_at"]:
                            should_write = False # Local is newer, potential conflict
                            results["conflicts"] += 1
                    
                    if should_write:
                        try:
                            content = base64.b64decode(f_info["content"])
                            with open(target_file, "wb") as f:
                                f.write(content)
                            os.utime(target_file, (f_info["modified_at"], f_info["modified_at"]))
                            results["applied"] += 1
                        except Exception as e:
                            logger.error(f"Failed to write sync file: {f_info['path']} - {e}")
                
                # 4. Log sync audit
                conn.execute("""
                    INSERT INTO sync_audit_logs (user_id, device_id, action_type, target_sector, status, payload_summary)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (package.user_id, package.device_id, SyncAction.DOWNLOAD, "workspace", SyncStatus.SUCCESS, json.dumps(results)))
                
                # Update device last_sync
                conn.execute("UPDATE sync_devices SET last_sync = ? WHERE device_id = ?", (datetime.now(), package.device_id))
                
                conn.commit()
                
        return results

sync_manager = SyncManager()
