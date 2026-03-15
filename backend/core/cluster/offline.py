import logging
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from backend.core.database import db_manager
from .mesh import mesh_manager

logger = logging.getLogger(__name__)

class SyncItem(BaseModel):
    sync_id: str
    operation_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    status: str

class OfflineState(BaseModel):
    is_offline: bool
    backlog_count: int
    last_sync: Optional[datetime]
    operation_mode: str # mesh, autonomous

class OfflineManager:
    """
    Handles autonomous node operation during network disconnection.
    Phase 27 - Local Survival Runtime.
    """
    def __init__(self):
        self.is_offline = False
        self._running = False
        self._check_task = None

    async def start(self):
        if self._running: return
        self._running = True
        self._check_task = asyncio.create_task(self._connectivity_monitor())
        logger.info("OfflineManager: Local survival runtime active.")

    async def queue_operation(self, op_type: str, payload: Dict[str, Any]):
        """Buffers an operation for later synchronization."""
        sync_id = str(uuid.uuid4())
        query = """
        INSERT INTO cluster_sync_backlog (sync_id, operation_type, payload, status)
        VALUES (:id, :type, :payload, 'pending')
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {
                "id": sync_id, "type": op_type, "payload": payload
            })
            await session.commit()
        logger.info(f"OfflineManager: Buffered {op_type} operation ({sync_id})")

    async def get_offline_state(self) -> OfflineState:
        async with db_manager.get_session() as session:
            row = await session.execute("SELECT count(*) as count FROM cluster_sync_backlog WHERE status = 'pending'")
            count = row.fetchone()["count"]
            
            return OfflineState(
                is_offline=self.is_offline,
                backlog_count=count,
                last_sync=None, # To be implemented with sync history
                operation_mode="autonomous" if self.is_offline else "mesh"
            )

    async def _connectivity_monitor(self):
        """Monitors mesh health to detect disconnection."""
        while self._running:
            try:
                mesh_state = await mesh_manager.get_mesh_state()
                was_offline = self.is_offline
                
                # Threshold: No active peers = Offline
                self.is_offline = mesh_state.connected_peers == 0
                
                if self.is_offline and not was_offline:
                    logger.warning("OfflineManager: Network loss detected. Entering AUTONOMOUS MODE.")
                elif not self.is_offline and was_offline:
                    logger.info("OfflineManager: Connectivity restored. Initiating RECONCILIATION.")
                    await self.reconcile_state()
                    
            except Exception as e:
                logger.error(f"OfflineManager Monitor Error: {e}")
            await asyncio.sleep(15)

    async def reconcile_state(self):
        """Synchronizes buffered operations with the wider cluster."""
        async with db_manager.get_session() as session:
            rows = await session.execute(
                "SELECT * FROM cluster_sync_backlog WHERE status = 'pending' ORDER BY timestamp ASC"
            )
            pending_items = rows.fetchall()
            
            if not pending_items:
                return

            logger.info(f"OfflineManager: Synchronizing {len(pending_items)} items...")
            
            for item in pending_items:
                success = await self._dispatch_sync_item(item)
                if success:
                    await session.execute(
                        "UPDATE cluster_sync_backlog SET status = 'completed' WHERE sync_id = :id",
                        {"id": item["sync_id"]}
                    )
            
            await session.commit()
            logger.info("OfflineManager: Reconciliation complete.")

    async def _dispatch_sync_item(self, item) -> bool:
        """Sends a buffered item to the mesh/central registry."""
        # Simulated sync logic
        # In Phase 27, we log the sync event
        logger.debug(f"Syncing {item['operation_type']}...")
        await asyncio.sleep(0.5) 
        return True

offline_manager = OfflineManager()
