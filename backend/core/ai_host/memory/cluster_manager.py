import logging
import uuid
import time
import json
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .knowledge_graph import knowledge_graph

logger = logging.getLogger(__name__)

class IdeaCluster(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    tags: List[str] = []
    node_ids: List[str] = [] # IDs of Knowledge Nodes
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

class ClusterManager:
    """
    Groups related knowledge nodes into semantic clusters and persists them.
    """
    def __init__(self):
        self.clusters: Dict[str, IdeaCluster] = {}
        self._load_clusters()

    def _load_clusters(self):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM ai_host_clusters").fetchall()
                    for row in rows:
                        cluster = IdeaCluster(
                            id=row["id"],
                            title=row["title"],
                            description=row["description"],
                            tags=json.loads(row["tags"]) if row["tags"] else [],
                            node_ids=json.loads(row["node_ids"]) if row["node_ids"] else [],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"]
                        )
                        self.clusters[cluster.id] = cluster
            logger.info(f"[CLUSTER_LOAD] Loaded {len(self.clusters)} clusters.")
        except Exception as e:
            logger.error(f"[CLUSTER_LOAD_ERROR] {e}")

    def create_cluster(self, title: str, description: str = "", node_ids: List[str] = []) -> IdeaCluster:
        cluster = IdeaCluster(title=title, description=description, node_ids=node_ids)
        self.clusters[cluster.id] = cluster
        self._persist_cluster(cluster)
        return cluster

    def _persist_cluster(self, cluster: IdeaCluster):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO ai_host_clusters (id, title, description, tags, node_ids, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cluster.id, cluster.title, cluster.description,
                        json.dumps(cluster.tags), json.dumps(cluster.node_ids),
                        cluster.created_at, cluster.updated_at
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"[CLUSTER_PERSIST_ERROR] {e}")

    def auto_group_ideas(self) -> List[IdeaCluster]:
        """
        Groups knowledge nodes by shared tags or keywords in titles.
        """
        nodes = knowledge_graph.get_all_nodes()
        if not nodes:
            return []

        # Simple keyword overlap clustering
        # 1. Collect all tags
        tag_map: Dict[str, List[str]] = {}
        for node in nodes:
            for tag in node.tags:
                if tag not in tag_map:
                    tag_map[tag] = []
                if node.id not in tag_map[tag]:
                    tag_map[tag].append(node.id)

        # 2. Create clusters for tags with multiple nodes
        new_clusters = []
        for tag, node_ids in tag_map.items():
            if len(node_ids) >= 1:
                title = tag.capitalize()
                # Check if cluster already exists
                existing = [c for c in self.clusters.values() if c.title.lower() == title.lower()]
                if existing:
                    cluster = existing[0]
                    # Update nodes avoiding duplicates
                    updated = False
                    for nid in node_ids:
                        if nid not in cluster.node_ids:
                            cluster.node_ids.append(nid)
                            updated = True
                    if updated:
                        cluster.updated_at = time.time()
                        self._persist_cluster(cluster)
                else:
                    cluster = self.create_cluster(
                        title=title,
                        description=f"Automatic cluster for nodes tagged with '{tag}'.",
                        node_ids=node_ids
                    )
                    cluster.tags = [tag]
                    self._persist_cluster(cluster)
                    new_clusters.append(cluster)
        
        return new_clusters

    def get_cluster(self, cluster_id: str) -> Optional[IdeaCluster]:
        return self.clusters.get(cluster_id)

    def get_all_clusters(self) -> List[IdeaCluster]:
        return list(self.clusters.values())

    def get_cluster_by_title(self, title: str) -> Optional[IdeaCluster]:
        import unicodedata
        def norm(t): return "".join(c for c in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(c) != 'Mn')
        target = norm(title)
        for c in self.clusters.values():
            if norm(c.title) == target or target in norm(c.title):
                return c
        return None

cluster_manager = ClusterManager()
