import logging
import asyncio
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from backend.core.database import db_manager
from .models import ClusterNode

logger = logging.getLogger(__name__)

class PeerInfo(BaseModel):
    node_id: str
    address: str
    region: str
    latency: float
    last_seen: datetime
    status: str

class MeshState(BaseModel):
    node_id: str
    connected_peers: int
    peers: List[PeerInfo]
    network_health: float # 0.0 to 1.0 based on connectivity
    latency_map: Dict[str, float]

class MeshManager:
    """
    Peer-to-Peer Mesh Networking Layer.
    Phase 26 - Decentralized Cluster Communication.
    """
    def __init__(self):
        self.local_node_id = "primary-node-01" # Default bootstrap
        self._running = False
        self._gossip_task = None

    async def start(self):
        if self._running: return
        self._running = True
        self._gossip_task = asyncio.create_task(self._gossip_loop())
        logger.info("MeshManager: Layer activated.")

    async def discover_peers(self):
        """Bootstraps peer discovery from the central node registry."""
        query = "SELECT node_id, node_url, node_region FROM cluster_nodes WHERE node_id != :local_id"
        async with db_manager.get_session() as session:
            rows = await session.execute(query, {"local_id": self.local_node_id})
            for row in rows:
                await self.add_peer(row["node_id"], row["node_url"], row["node_region"])

    async def add_peer(self, node_id: str, address: str, region: str):
        """Adds or updates a peer in the mesh."""
        query = """
        INSERT INTO cluster_peers (node_id, peer_address, peer_region, status)
        VALUES (:id, :addr, :region, 'connected')
        ON CONFLICT (node_id) DO UPDATE SET
            peer_address = EXCLUDED.peer_address,
            last_seen = CURRENT_TIMESTAMP
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {"id": node_id, "addr": address, "region": region})
            await session.commit()
        logger.info(f"MeshManager: Peer {node_id} integrated into mesh.")

    async def process_p2p_message(self, sender_id: str, payload: Dict[str, Any]):
        """Handles direct messages from peers."""
        # Update last seen on message receipt
        async with db_manager.get_session() as session:
            await session.execute(
                "UPDATE cluster_peers SET last_seen = CURRENT_TIMESTAMP, status = 'connected' WHERE node_id = :id",
                {"id": sender_id}
            )
            await session.commit()
        
        msg_type = payload.get("type", "ping")
        logger.debug(f"MeshManager: Received {msg_type} from {sender_id}")
        return {"status": "ok", "echo_type": msg_type}

    async def get_mesh_state(self) -> MeshState:
        """Aggregates local mesh view for Mission Control."""
        async with db_manager.get_session() as session:
            rows = await session.execute("SELECT * FROM cluster_peers")
            peers = []
            latency_map = {}
            total_latency = 0.0
            connected_count = 0
            
            for row in rows:
                peer = PeerInfo(
                    node_id=row["node_id"],
                    address=row["peer_address"],
                    region=row["peer_region"],
                    latency=row["latency"],
                    last_seen=row["last_seen"],
                    status=row["status"]
                )
                peers.append(peer)
                latency_map[peer.node_id] = peer.latency
                if peer.status == 'connected':
                    connected_count += 1
                    total_latency += peer.latency

            health = connected_count / len(peers) if peers else 1.0
            
            return MeshState(
                node_id=self.local_node_id,
                connected_peers=connected_count,
                peers=peers,
                network_health=health,
                latency_map=latency_map
            )

    async def _gossip_loop(self):
        """Periodic background gossip and health checks."""
        while self._running:
            try:
                # 1. Self-discovery (Bootstrap)
                await self.discover_peers()
                
                # 2. Ping peers (Simulated)
                async with db_manager.get_session() as session:
                    rows = await session.execute("SELECT node_id FROM cluster_peers")
                    for row in rows:
                        # In real P2P, we would perform a physical HTTP/TCP ping
                        # Here we simulate with random latency
                        import random
                        lat = random.uniform(5.0, 50.0)
                        await session.execute(
                            "UPDATE cluster_peers SET latency = :lat, last_seen = CURRENT_TIMESTAMP WHERE node_id = :id",
                            {"lat": lat, "id": row["node_id"]}
                        )
                    await session.commit()
            except Exception as e:
                logger.error(f"MeshManager Gossip Error: {e}")
            await asyncio.sleep(20)

mesh_manager = MeshManager()
