import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.core.database import db_manager
from backend.core.knowledge_graph.graph_models import KnowledgeNode, KnowledgeEdge

class GraphStore:
    """
    Persistent Graph Storage Layer for OmniWeb Knowledge Graph.
    Uses relational SQLite to represent nodes and edges.
    """
    def __init__(self):
        self.db_manager = db_manager

    def save_node(self, node: KnowledgeNode) -> int:
        """
        Saves a node to the Knowledge Graph or updates it if it exists.
        Returns the node ID.
        """
        with self.db_manager.get_connection() as conn:
            # Check if this node type + name already exists
            existing = conn.execute(
                "SELECT id FROM knowledge_nodes WHERE node_type = ? AND name = ?",
                (node.node_type, node.name)
            ).fetchone()

            if existing:
                node_id = existing["id"]
                conn.execute(
                    "UPDATE knowledge_nodes SET description = ?, importance_score = ?, metadata = ? WHERE id = ?",
                    (node.description, node.importance_score, json.dumps(node.metadata), node_id)
                )
                return node_id
            else:
                cursor = conn.execute(
                    "INSERT INTO knowledge_nodes (node_type, name, description, importance_score, metadata) VALUES (?, ?, ?, ?, ?)",
                    (node.node_type, node.name, node.description, node.importance_score, json.dumps(node.metadata))
                )
                return cursor.lastrowid

    def save_edge(self, edge: KnowledgeEdge) -> int:
        """
        Saves an edge between two nodes. 
        If an edge with same source, target and relationship already exists, update its weight.
        """
        with self.db_manager.get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM knowledge_edges WHERE source_node = ? AND target_node = ? AND relationship = ?",
                (edge.source_node, edge.target_node, edge.relationship)
            ).fetchone()

            if existing:
                edge_id = existing["id"]
                conn.execute(
                    "UPDATE knowledge_edges SET weight = ?, metadata = ? WHERE id = ?",
                    (edge.weight, json.dumps(edge.metadata), edge_id)
                )
                return edge_id
            else:
                cursor = conn.execute(
                    "INSERT INTO knowledge_edges (source_node, target_node, relationship, weight, metadata) VALUES (?, ?, ?, ?, ?)",
                    (edge.source_node, edge.target_node, edge.relationship, edge.weight, json.dumps(edge.metadata))
                )
                return cursor.lastrowid

    def get_node(self, node_id: int) -> Optional[KnowledgeNode]:
        """Retrieves a single node by ID."""
        with self.db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM knowledge_nodes WHERE id = ?", (node_id,)).fetchone()
            if row:
                return KnowledgeNode(
                    id=row["id"],
                    node_type=row["node_type"],
                    name=row["name"],
                    description=row["description"],
                    created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
                    importance_score=row["importance_score"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                )
        return None

    def find_node_by_name(self, name: str, node_type: Optional[str] = None) -> Optional[KnowledgeNode]:
        """Finds a node by name, optionally filtering by type."""
        with self.db_manager.get_connection() as conn:
            query = "SELECT * FROM knowledge_nodes WHERE name = ?"
            params = [name]
            if node_type:
                query += " AND node_type = ?"
                params.append(node_type)
            
            row = conn.execute(query, params).fetchone()
            if row:
                return KnowledgeNode(
                    id=row["id"],
                    node_type=row["node_type"],
                    name=row["name"],
                    description=row["description"],
                    created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
                    importance_score=row["importance_score"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                )
        return None

    def get_neighbors(self, node_id: int) -> List[Dict[str, Any]]:
        """Retrieves direct neighbors with edge information."""
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("""
                SELECT e.*, n.name as neighbor_name, n.node_type as neighbor_type
                FROM knowledge_edges e
                JOIN knowledge_nodes n ON e.target_node = n.id
                WHERE e.source_node = ?
                UNION
                SELECT e.*, n.name as neighbor_name, n.node_type as neighbor_type
                FROM knowledge_edges e
                JOIN knowledge_nodes n ON e.source_node = n.id
                WHERE e.target_node = ?
            """, (node_id, node_id)).fetchall()
            
            return [dict(row) for row in rows]

    def get_all_nodes(self) -> List[KnowledgeNode]:
        """Retrieves all nodes in the graph."""
        with self.db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM knowledge_nodes").fetchall()
            return [KnowledgeNode(
                id=row["id"],
                node_type=row["node_type"],
                name=row["name"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
                importance_score=row["importance_score"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            ) for row in rows]
