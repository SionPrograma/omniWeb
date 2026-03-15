import logging
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.core.database import db_manager
from .models import ChipTask, TaskStatus, WorkloadState, ClusterNode, NodeStatus, NodeRole
from .manager import cluster_manager
from .offline import offline_manager

logger = logging.getLogger(__name__)

class WorkloadRouter:
    """
    Dispatcher for Chip execution tasks across worker nodes.
    Phase 25 - Workload Distribution.
    """

    async def submit_task(self, chip_slug: str, context: Dict[str, Any], user_id: str) -> str:
        """Entry point for distributing a chip task."""
        task_id = str(uuid.uuid4())
        
        # 1. Register pending task
        query = """
        INSERT INTO cluster_tasks (task_id, chip_slug, requesting_user_id, execution_context, status)
        VALUES (:id, :slug, :user, :ctx, 'pending')
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {
                "id": task_id, "slug": chip_slug, "user": user_id, "ctx": context
            })
            await session.commit()

        # 2. Dispatch task (async background)
        asyncio.create_task(self._dispatch_logic(task_id))
        
        return task_id

    async def _dispatch_logic(self, task_id: str):
        """Internal logic to find a node and send the task."""
        # 1. Get task info
        task = await self.get_task(task_id)
        if not task: return

        # 2. Select Worker Node (Strategy: Least Load)
        if offline_manager.is_offline:
            logger.info(f"WorkloadRouter: Node Offline. Executing task {task_id} LOCALLY.")
            # Map to self for local execution
            local_node_id = "primary-node-01" 
            await self._update_task_status(task_id, TaskStatus.RUNNING, node_id=local_node_id)
            
            # Simulate local work
            await asyncio.sleep(1)
            result = {"outcome": "success", "mode": "autonomous"}
            await self._complete_task(task_id, result)
            
            # Buffer for cluster sync
            await offline_manager.queue_operation("task_completion", {
                "task_id": task_id, "chip_slug": task.chip_slug, "result": result
            })
            return

        node = await self._select_worker_node()
        if not node:
            logger.error(f"WorkloadRouter: No available workers for task {task_id}")
            await self._update_task_status(task_id, TaskStatus.FAILED, error="No workers available")
            return

        # 3. Mark as running
        await self._update_task_status(task_id, TaskStatus.RUNNING, node_id=node.node_id)

        # 4. Dispatch (Simulated HTTP call to worker in Phase 25)
        # In a real distributed system, we would POST to node.node_url/api/v1/worker/execute
        logger.info(f"WorkloadRouter: Dispatching task {task_id} to node {node.node_id}")
        
        # Simulate execution latency
        await asyncio.sleep(2) 

        # 5. Handle Result (Simulated success)
        result = {"outcome": "success", "message": f"Processed by {node.node_id}"}
        await self._complete_task(task_id, result)

    async def _select_worker_node(self) -> Optional[ClusterNode]:
        """Node Selection Strategy: Healthy, Least CPU, Least Active Chips."""
        cluster_state = await cluster_manager.get_cluster_state()
        workers = [
            n for n in cluster_state.nodes 
            if n.node_role == NodeRole.WORKER and n.node_status == NodeStatus.ONLINE
        ]
        
        if not workers:
            # Fallback to Primary if allowed, but here we enforce Worker role
            return None
            
        # Tie-breaker: CPU usage * 100 + active_chips
        return min(workers, key=lambda n: (n.cpu_usage * 100) + n.active_chips)

    async def get_task(self, task_id: str) -> Optional[ChipTask]:
        async with db_manager.get_session() as session:
            row = await session.execute(
                "SELECT * FROM cluster_tasks WHERE task_id = :id", {"id": task_id}
            )
            row_data = row.fetchone()
            return ChipTask(**dict(row_data)) if row_data else None

    async def _update_task_status(self, task_id: str, status: TaskStatus, node_id: str = None, error: str = None):
        params = {"status": status, "id": task_id, "node_id": node_id, "error": error}
        query = """
        UPDATE cluster_tasks SET 
            status = :status, 
            worker_node_id = COALESCE(:node_id, worker_node_id),
            error_message = :error,
            started_at = CASE WHEN :status = 'running' THEN CURRENT_TIMESTAMP ELSE started_at END
        WHERE task_id = :id
        """
        async with db_manager.get_session() as session:
            await session.execute(query, params)
            await session.commit()

    async def _complete_task(self, task_id: str, result: Dict[str, Any]):
        query = """
        UPDATE cluster_tasks SET 
            status = 'completed', 
            result_payload = :res,
            completed_at = CURRENT_TIMESTAMP
        WHERE task_id = :id
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {"res": result, "id": task_id})
            await session.commit()
        logger.info(f"WorkloadRouter: Task {task_id} completed successfully.")

    async def get_workload_state(self) -> WorkloadState:
        """Retrieves cluster-wide workload status."""
        async with db_manager.get_session() as session:
            rows = await session.execute("SELECT * FROM cluster_tasks ORDER BY created_at DESC LIMIT 50")
            all_tasks = [ChipTask(**dict(r)) for r in rows]
            
            active = len([t for t in all_tasks if t.status == TaskStatus.RUNNING])
            queued = len([t for t in all_tasks if t.status == TaskStatus.PENDING])
            complete = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
            failed = len([t for t in all_tasks if t.status == TaskStatus.FAILED])
            
            dist = {}
            for t in all_tasks:
                if t.status == TaskStatus.RUNNING and t.worker_node_id:
                    dist[t.worker_node_id] = dist.get(t.worker_node_id, 0) + 1

            return WorkloadState(
                active_tasks=active,
                queued_tasks=queued,
                completed_tasks=complete,
                failed_tasks=failed,
                worker_distribution=dist,
                avg_task_latency=120.5, # Mock value for now
                tasks=all_tasks
            )

    async def check_and_reassign_tasks(self):
        """Failover Handler: Reassign tasks from offline nodes."""
        async with db_manager.get_session() as session:
            # Find running tasks on offline nodes
            query = """
            SELECT t.task_id FROM cluster_tasks t
            JOIN cluster_nodes n ON t.worker_node_id = n.node_id
            WHERE t.status = 'running' AND n.node_status = 'offline'
            """
            rows = await session.execute(query)
            stale_tasks = [r["task_id"] for r in rows]
            
            for tid in stale_tasks:
                logger.warning(f"WorkloadRouter: Node failure detected for task {tid}. Reassigning...")
                await self._update_task_status(tid, TaskStatus.PENDING)
                asyncio.create_task(self._dispatch_logic(tid))

workload_router = WorkloadRouter()
