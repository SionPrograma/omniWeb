import json
import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .models import GraphNode, GraphEdge, GraphQueryResponse
from backend.core.user_logbook.models import UserLogbookEntry, UserEntryType

logger = logging.getLogger(__name__)

class UserGraphEngine:
    """
    Manages the building and querying of the Personal Knowledge Graph.
    Phase 18: User Semantic Memory Graph.
    """

    def save_node(self, node: GraphNode):
        from backend.core.permissions import enforce_permission, USER_GRAPH_ACCESS
        enforce_permission(USER_GRAPH_ACCESS)
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Deduplicate by entry_id for a specific user
                if node.entry_id:
                    existing = conn.execute(
                        "SELECT id FROM user_graph_nodes WHERE user_id = ? AND entry_id = ?",
                        (node.user_id, node.entry_id)
                    ).fetchone()
                    if existing:
                        node.id = existing["id"]

                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_graph_nodes (id, user_id, entry_id, node_type, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (node.id, node.user_id, node.entry_id, node.node_type, node.content, 
                     node.timestamp.isoformat(), json.dumps(node.metadata))
                )
                conn.commit()

    def save_edge(self, edge: GraphEdge):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                existing = conn.execute(
                    "SELECT id FROM user_graph_edges WHERE user_id = ? AND source_node = ? AND target_node = ? AND relation_type = ?",
                    (edge.user_id, edge.source_node, edge.target_node, edge.relation_type)
                ).fetchone()
                if existing:
                    edge.id = existing["id"]

                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_graph_edges (id, user_id, source_node, target_node, relation_type, confidence_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (edge.id, edge.user_id, edge.source_node, edge.target_node, 
                     edge.relation_type, edge.confidence_score, json.dumps(edge.metadata))
                )
                conn.commit()

    async def build_from_logbook(self, user_id: str):
        """
        Scans user logbook entries and builds the semantic graph.
        """
        from backend.core.user_logbook.manager import logbook_manager
        entries = logbook_manager.list_entries(user_id, limit=200)
        
        nodes = []
        # 1. Create Nodes from entries
        for entry in entries:
            node = GraphNode(
                user_id=user_id,
                entry_id=entry.id,
                node_type=entry.entry_type.value,
                content=entry.content,
                timestamp=entry.timestamp,
                metadata=entry.metadata
            )
            self.save_node(node)
            nodes.append(node)

        # 2. Detect Relationships (Semantic Analysis Prototype)
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                # Relationship Detection Heuristics
                relation = self._detect_relation(node_a, node_b)
                if relation:
                    edge = GraphEdge(
                        user_id=user_id,
                        source_node=node_a.id,
                        target_node=node_b.id,
                        relation_type=relation["type"],
                        confidence_score=relation["confidence"]
                    )
                    self.save_edge(edge)

        logger.info(f"Graph rebuilt for user {user_id}: {len(nodes)} nodes processed.")

    def _detect_relation(self, node_a: GraphNode, node_b: GraphNode) -> Optional[Dict[str, Any]]:
        """
        Heuristic-based relationship detection.
        In Phase 18, this uses keyword overlap and temporal proximity.
        """
        # A. Keyword Overlap (Related To)
        words_a = set(re.findall(r'\w+', node_a.content.lower()))
        words_b = set(re.findall(r'\w+', node_b.content.lower()))
        common = words_a.intersection(words_b)
        # Filter stop-words or short words
        meaningful = {w for w in common if len(w) > 3}
        
        if len(meaningful) >= 1:
            return {"type": "related_to", "confidence": min(1.0, 0.5 + (len(meaningful) * 0.1))}

        # B. Dependency Hints (depends_on)
        if "depend" in node_a.content.lower() and any(w in node_a.content.lower() for w in words_b):
             return {"type": "depends_on", "confidence": 0.8}

        # C. Mention of specific entities (mentions_chip)
        # (This would use the module registry in a full implementation)
        
        return None

    def get_user_graph(self, user_id: str) -> GraphQueryResponse:
        from backend.core.permissions import enforce_permission, USER_GRAPH_ACCESS
        enforce_permission(USER_GRAPH_ACCESS)
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                node_rows = conn.execute("SELECT * FROM user_graph_nodes WHERE user_id = ?", (user_id,)).fetchall()
                edge_rows = conn.execute("SELECT * FROM user_graph_edges WHERE user_id = ?", (user_id,)).fetchall()
                
                nodes = [GraphNode(
                    id=row["id"],
                    user_id=row["user_id"],
                    entry_id=row["entry_id"],
                    node_type=row["node_type"],
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                ) for row in node_rows]
                
                edges = [GraphEdge(
                    id=row["id"],
                    user_id=row["user_id"],
                    source_node=row["source_node"],
                    target_node=row["target_node"],
                    relation_type=row["relation_type"],
                    confidence_score=row["confidence_score"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                ) for row in edge_rows]
                
                return GraphQueryResponse(nodes=nodes, edges=edges)

    def get_neighbors(self, user_id: str, node_id: str) -> List[Dict[str, Any]]:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT e.*, n.content as neighbor_content, n.node_type as neighbor_type
                    FROM user_graph_edges e
                    JOIN user_graph_nodes n ON e.target_node = n.id
                    WHERE e.source_node = ? AND e.user_id = ?
                    UNION
                    SELECT e.*, n.content as neighbor_content, n.node_type as neighbor_type
                    FROM user_graph_edges e
                    JOIN user_graph_nodes n ON e.source_node = n.id
                    WHERE e.target_node = ? AND e.user_id = ?
                    """,
                    (node_id, user_id, node_id, user_id)
                ).fetchall()
                return [dict(row) for row in rows]

user_graph_engine = UserGraphEngine()
