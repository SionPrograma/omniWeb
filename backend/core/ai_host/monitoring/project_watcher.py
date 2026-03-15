import logging
import os
import time
import uuid
import json
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from ..memory.project_manager import project_manager, ProjectLineage

logger = logging.getLogger(__name__)

class ProjectActivityEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_slug: str
    event_type: str # MODIFIED, CREATED, DELETED
    file_path: str
    summary: str
    created_at: float = Field(default_factory=time.time)
    related_lineage_id: Optional[str] = None

class ProjectWatcher:
    """
    Monitors physical project directories for changes.
    Detects modifications and records them as semantic activity events.
    """
    def __init__(self):
        self.last_scanned: Dict[str, float] = {} # project_slug -> last scan timestamp
        self.events: List[ProjectActivityEvent] = []
        self._load_recent_activity()

    def _load_recent_activity(self):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM ai_host_project_activity ORDER BY created_at DESC LIMIT 100").fetchall()
                    for row in rows:
                        event = ProjectActivityEvent(
                            id=row["id"],
                            project_slug=row["project_slug"],
                            event_type=row["event_type"],
                            file_path=row["file_path"],
                            summary=row["summary"],
                            created_at=row["created_at"],
                            related_lineage_id=row["related_lineage_id"]
                        )
                        self.events.append(event)
            logger.info(f"[WATCHER_LOAD] Loaded {len(self.events)} recent activity events.")
        except Exception as e:
            logger.error(f"[WATCHER_LOAD_ERROR] {e}")

    def scan_all_projects(self) -> List[ProjectActivityEvent]:
        """
        Polls initialized projects for file modifications.
        """
        new_events = []
        lineages = list(project_manager.lineages.values())
        
        for lineage in lineages:
            events = self.scan_project(lineage)
            new_events.extend(events)
            
        return new_events

    def scan_project(self, lineage: ProjectLineage) -> List[ProjectActivityEvent]:
        """
        Scans a specific project directory for changes.
        """
        project_slug = lineage.project_slug
        project_path = os.path.join(project_manager.base_chips_path, f"chip-{project_slug}")
        
        if not os.path.exists(project_path):
            logger.warning(f"[WATCHER_SCAN] Project path not found: {project_path}")
            return []

        # Use the lineage's updated_at or the last scan time as reference
        last_scan = self.last_scanned.get(project_slug, 0)
        now = time.time()
        
        # Debounce: avoid scanning the same project more than once every 30 seconds 
        if now - last_scan < 30:
            logger.debug(f"[WATCHER_SCAN] Skipping redundant scan for {project_slug} (Too soon).")
            return []

        last_reference = lineage.updated_at
        new_events = []
        
        # Expanded ignore list
        ignore_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv", "dist", "build", ".next", ".antigravity"}

        # Recursively scan for modified files
        for root, dirs, files in os.walk(project_path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                fpath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(fpath)
                except OSError:
                    continue # Skip files that might have been deleted/moved during scan
                
                if mtime > last_reference:
                    rel_path = os.path.relpath(fpath, project_path)
                    
                    # Record Event
                    event = ProjectActivityEvent(
                        project_slug=project_slug,
                        event_type="MODIFIED",
                        file_path=rel_path,
                        summary=f"Cambio detectado en {rel_path}.",
                        related_lineage_id=lineage.id
                    )
                    new_events.append(event)
                    
                    # Update lineage in-memory
                    lineage.updated_at = max(lineage.updated_at, mtime)
                    lineage.related_events.append({
                        "type": "modified",
                        "timestamp": mtime,
                        "message": f"Source modification: {rel_path}"
                    })

        if new_events:
            # Batch Persist Events
            self._persist_events_batch(new_events)
            # Update lineage in DB
            project_manager._persist_lineage(lineage)

        self.last_scanned[project_slug] = time.time()
        self.events.extend(new_events)
        return new_events

    def _persist_events_batch(self, events: List[ProjectActivityEvent]):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.executemany("""
                        INSERT OR REPLACE INTO ai_host_project_activity 
                        (id, project_slug, event_type, file_path, summary, created_at, related_lineage_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, [
                        (e.id, e.project_slug, e.event_type, e.file_path, e.summary, e.created_at, e.related_lineage_id)
                        for e in events
                    ])
                    conn.commit()
            logger.debug(f"[WATCHER_BATCH] Persisted {len(events)} events.")
        except Exception as e:
            logger.error(f"[WATCHER_BATCH_ERROR] {e}")

    def _persist_event(self, event: ProjectActivityEvent):
        """Deprecated: Use _persist_events_batch instead."""
        self._persist_events_batch([event])

    def get_recent_activity(self, project_slug: Optional[str] = None, limit: int = 10) -> List[ProjectActivityEvent]:
        if project_slug:
            filtered = [e for e in self.events if e.project_slug == project_slug]
        else:
            filtered = self.events
            
        return sorted(filtered, key=lambda x: x.created_at, reverse=True)[:limit]

project_watcher = ProjectWatcher()
