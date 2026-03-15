import logging
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.database import db_manager
from backend.core.cluster.manager import cluster_manager
from backend.core.cluster.models import NodeStatus

logger = logging.getLogger(__name__)

class ScalingManager:
    """Phase 46: Global Edge Node Layer."""
    async def get_edge_nodes(self) -> List[Dict[str, Any]]:
        async with db_manager.get_session() as session:
            res = await session.execute("SELECT * FROM edge_node_metadata WHERE is_active = TRUE")
            return [dict(r) for r in res]

    async def register_edge_node(self, node_id: str, region: str):
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO edge_node_metadata (node_id, region_code)
                VALUES (:nid, :reg)
                ON CONFLICT (node_id) DO UPDATE SET region_code = EXCLUDED.region_code
            """, {"nid": node_id, "reg": region})
            await session.commit()
            
class ObservabilityManager:
    """Phase 47: Global Observability System."""
    async def record_metric(self, node_id: str, service: str, metric: str, value: float):
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO system_telemetry (telemetry_id, node_id, service_name, metric_name, metric_value)
                VALUES (:tid, :nid, :svc, :met, :val)
            """, {
                "tid": str(uuid.uuid4()), "nid": node_id, "svc": service, "met": metric, "val": value
            })
            await session.commit()

    async def get_cluster_metrics(self) -> List[Dict[str, Any]]:
        async with db_manager.get_session() as session:
            # Last 50 metrics for visualization
            res = await session.execute("SELECT * FROM system_telemetry ORDER BY timestamp DESC LIMIT 50")
            return [dict(r) for r in res]

scaling_manager = ScalingManager()
observability_manager = ObservabilityManager()
