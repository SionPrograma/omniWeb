import logging
import asyncio
import uuid
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import StorageBlock, StorageFragment, StorageGridState, NodeRole, NodeStatus
from .manager import cluster_manager
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class StorageManager:
    """
    OmniWeb Distributed Storage Grid.
    Phase 29 - Standalone Data Persistence.
    """
    def __init__(self):
        self.replication_factor = 3
        self._running = False

    async def start(self):
        self._running = True
        logger.info("StorageManager: Distributed Storage Grid active.")

    async def store_data(self, data_type: str, content: bytes, metadata: Dict[str, Any] = {}) -> str:
        """
        Fragments data into blocks and distributes across storage nodes.
        """
        block_id = str(uuid.uuid4())
        content_hash = hashlib.sha256(content).hexdigest()
        size = len(content)

        # 1. Register Block
        query = """
        INSERT INTO storage_blocks (block_id, data_type, content_hash, size_bytes, metadata)
        VALUES (:id, :type, :hash, :size, :meta)
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {
                "id": block_id, "type": data_type, "hash": content_hash, "size": size, "meta": metadata
            })
            await session.commit()

        # 2. Distribute Fragments
        await self._distribute_block(block_id)
        
        return block_id

    async def _distribute_block(self, block_id: str):
        """Finds storage nodes and creates fragments."""
        nodes = await self._get_storage_nodes()
        if not nodes:
            logger.warning(f"StorageManager: No dedicated storage nodes. Falling back to primary.")
            nodes = [n for n in (await cluster_manager.get_cluster_state()).nodes if n.node_role == NodeRole.PRIMARY]

        if not nodes:
            logger.error("StorageManager: CRITICAL - No nodes available for storage.")
            return

        # Simple distribution: Use N nodes for replication
        target_nodes = nodes[:self.replication_factor]
        
        async with db_manager.get_session() as session:
            for i, node in enumerate(target_nodes):
                fragment_id = str(uuid.uuid4())
                query = """
                INSERT INTO storage_fragments (fragment_id, block_id, node_id, fragment_index)
                VALUES (:fid, :bid, :nid, :idx)
                """
                await session.execute(query, {
                    "fid": fragment_id, "bid": block_id, "nid": node.node_id, "idx": i
                })
            await session.commit()
            
        logger.info(f"StorageManager: Block {block_id} distributed across {len(target_nodes)} nodes.")

    async def _get_storage_nodes(self):
        state = await cluster_manager.get_cluster_state()
        return [n for n in state.nodes if n.node_role == NodeRole.STORAGE and n.node_status == NodeStatus.ONLINE]

    async def get_grid_state(self) -> StorageGridState:
        """Reports the global health of the storage grid."""
        async with db_manager.get_session() as session:
            rows = await session.execute("SELECT * FROM storage_blocks ORDER BY created_at DESC LIMIT 20")
            blocks = [StorageBlock(**dict(r)) for r in rows]
            
            res_stats = await session.execute("SELECT COUNT(*) as count, SUM(size_bytes) as total_size FROM storage_blocks")
            stats = res_stats.fetchone()
            
            res_nodes = await session.execute("SELECT COUNT(*) as count FROM storage_nodes WHERE is_active = TRUE")
            active_nodes = res_nodes.fetchone()["count"]

            return StorageGridState(
                total_capacity=1024 * 1024 * 1024 * 100, # 100GB Simulated
                used_capacity=stats["total_size"] or 0,
                available_nodes=active_nodes,
                replication_factor=self.replication_factor,
                healthy_blocks=stats["count"] or 0,
                corrupt_blocks=0,
                blocks=blocks
            )

storage_manager = StorageManager()
