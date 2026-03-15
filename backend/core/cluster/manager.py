import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from backend.core.database import db_manager
from backend.core.config import settings
from .models import ClusterNode, NodeStatus, HeartbeatPayload, ClusterState, NodeRole

logger = logging.getLogger(__name__)

class ClusterManager:
    """
    Registry and control center for OmniWeb Cluster Nodes.
    Phase 24 - Distributed Infrastructure.
    """
    
    def __init__(self):
        self._monitoring_task = None
        self._running = False

    async def register_node(self, node_data: Dict[str, Any]):
        """Registers or updates a node in the cluster."""
        query = """
        INSERT INTO cluster_nodes (
            node_id, node_role, node_region, node_status, node_url, node_secret, connected_services
        ) VALUES (
            :node_id, :node_role, :node_region, 'online', :node_url, :node_secret, :connected_services
        )
        ON CONFLICT (node_id) DO UPDATE SET
            node_url = EXCLUDED.node_url,
            node_status = 'online',
            last_heartbeat = CURRENT_TIMESTAMP
        """
        async with db_manager.get_session() as session:
            await session.execute(query, node_data)
            await session.commit()
        logger.info(f"ClusterManager: Node {node_data['node_id']} registered.")

    async def process_heartbeat(self, payload: HeartbeatPayload):
        """Updates node metrics and last_heartbeat."""
        query = """
        UPDATE cluster_nodes SET
            cpu_usage = :cpu,
            memory_usage = :mem,
            active_chips = :chips,
            latency = :lat,
            last_heartbeat = CURRENT_TIMESTAMP,
            node_status = CASE 
                WHEN node_status = 'offline' THEN 'online' 
                ELSE node_status 
            END
        WHERE node_id = :id
        """
        params = {
            "cpu": payload.cpu_usage,
            "mem": payload.memory_usage,
            "chips": payload.active_chips,
            "lat": payload.latency,
            "id": payload.node_id
        }
        async with db_manager.get_session() as session:
            await session.execute(query, params)
            await session.commit()

    async def get_cluster_state(self) -> ClusterState:
        """Retrieves comprehensive cluster state."""
        async with db_manager.get_session() as session:
            rows = await session.execute("SELECT * FROM cluster_nodes")
            nodes = []
            total_cpu = 0.0
            worker_count = 0
            storage_count = 0
            edge_count = 0
            active_count = 0
            
            for row in rows:
                node = ClusterNode(**dict(row))
                nodes.append(node)
                
                if node.node_status == NodeStatus.ONLINE:
                    active_count += 1
                
                if node.node_role == NodeRole.WORKER:
                    total_cpu += node.cpu_usage
                    worker_count += 1
                elif node.node_role == NodeRole.STORAGE:
                    storage_count += 1
                elif node.node_role == NodeRole.EDGE:
                    edge_count += 1
            
            avg_load = total_cpu / worker_count if worker_count > 0 else 0.0
            
            return ClusterState(
                active_nodes=active_count,
                total_nodes=len(nodes),
                nodes=nodes,
                cluster_load=avg_load,
                storage_nodes=storage_count,
                edge_nodes=edge_count
            )

    async def perform_node_operation(self, node_id: str, operation: str):
        """Executes maintenance operations on a node."""
        status_map = {
            "drain": NodeStatus.DRAINING,
            "disable": NodeStatus.OFFLINE,
            "enable": NodeStatus.ONLINE,
            "restart": NodeStatus.ONLINE # Simplified for simulation
        }
        
        if operation not in status_map and operation != "restart":
            raise ValueError(f"Invalid operation: {operation}")
            
        new_status = status_map.get(operation, NodeStatus.ONLINE)
        
        async with db_manager.get_session() as session:
            await session.execute(
                "UPDATE cluster_nodes SET node_status = :status WHERE node_id = :id",
                {"status": new_status, "id": node_id}
            )
            await session.commit()
        logger.warning(f"ClusterManager: Executed {operation} on node {node_id}. New Status: {new_status}")

    async def promote_to_primary(self, node_id: str):
        """Designates a node as the new primary (Failover Phase 24)."""
        async with db_manager.get_session() as session:
            # 1. Demote current primary
            await session.execute(
                "UPDATE cluster_nodes SET node_role = 'worker' WHERE node_role = 'primary'"
            )
            # 2. Promote target
            await session.execute(
                "UPDATE cluster_nodes SET node_role = 'primary' WHERE node_id = :id",
                {"id": node_id}
            )
            await session.commit()
        logger.critical(f"ClusterManager: FAILOVER TRIGGERED. New Primary: {node_id}")

    async def start_monitor(self):
        """Starts background heartbeat monitoring."""
        if self._running: return
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        """Check for timed-out nodes every 10 seconds."""
        while self._running:
            try:
                # Mark nodes offline if no heartbeat for > 60 seconds
                cutoff = datetime.utcnow() - timedelta(seconds=60)
                async with db_manager.get_session() as session:
                    await session.execute(
                        "UPDATE cluster_nodes SET node_status = 'offline' "
                        "WHERE last_heartbeat < :cutoff AND node_status != 'offline'",
                        {"cutoff": cutoff}
                    )
                    await session.commit()
                
                # Phase 25: Trigger task failover
                from .workload import workload_router
                await workload_router.check_and_reassign_tasks()

            except Exception as e:
                logger.error(f"ClusterManager Monitor Error: {e}")
            await asyncio.sleep(10)

cluster_manager = ClusterManager()
