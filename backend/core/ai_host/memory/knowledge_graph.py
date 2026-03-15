import logging
import uuid
import time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class KnowledgeNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    tags: List[str] = []
    connections: List[str] = [] # List of Node IDs
    metadata: Dict[str, Any] = {}
    created_at: float = Field(default_factory=time.time)

class KnowledgeGraph:
    """
    Handles structured knowledge nodes and their relationships.
    """
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self._load_graph()

    def _load_graph(self):
        """
        Loads persisted knowledge nodes and edges from SQLite into memory.
        """
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        import json

        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    # 1. Load Nodes
                    rows = conn.execute("SELECT * FROM ai_host_knowledge_nodes").fetchall()
                    for row in rows:
                        node = KnowledgeNode(
                            id=row["id"],
                            title=row["title"],
                            description=row["description"],
                            tags=json.loads(row["tags"]) if row["tags"] else [],
                            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                            created_at=row["created_at"]
                        )
                        self.nodes[node.id] = node

                    # 2. Load Edges
                    edge_rows = conn.execute("SELECT * FROM ai_host_knowledge_edges").fetchall()
                    for erow in edge_rows:
                        sid, tid = erow["source_id"], erow["target_id"]
                        if sid in self.nodes and tid in self.nodes:
                            if tid not in self.nodes[sid].connections:
                                self.nodes[sid].connections.append(tid)
                            if sid not in self.nodes[tid].connections:
                                self.nodes[tid].connections.append(sid)

            logger.info(f"[KNOWLEDGE_LOAD] Loaded {len(self.nodes)} nodes from persistent storage.")
        except Exception as e:
            logger.error(f"[KNOWLEDGE_LOAD_ERROR] Failed to load graph: {e}")

    def store_knowledge_node(self, title: str, content: str, tags: List[str] = []) -> KnowledgeNode:
        """
        Creates, stores in memory, and persists a new knowledge node.
        """
        node = KnowledgeNode(
            title=title,
            description=content,
            tags=tags
        )
        self.nodes[node.id] = node
        
        # Persistence
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        import json
        
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO ai_host_knowledge_nodes (id, title, description, tags, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        node.id, node.title, node.description, 
                        json.dumps(node.tags), json.dumps(node.metadata), node.created_at
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"[KNOWLEDGE_PERSIST_ERROR] {e}")

        logger.info(f"[KNOWLEDGE_NODE_CREATED] ID: {node.id} | Title: {node.title}")
        return node

    def link_knowledge_nodes(self, node_id_a: str, node_id_b: str) -> bool:
        """
        Creates a bidirectional link between two nodes in memory and SQLite.
        """
        if node_id_a in self.nodes and node_id_b in self.nodes:
            # Memory Link
            if node_id_b not in self.nodes[node_id_a].connections:
                self.nodes[node_id_a].connections.append(node_id_b)
            if node_id_a not in self.nodes[node_id_b].connections:
                self.nodes[node_id_b].connections.append(node_id_a)
            
            # DB Link
            from backend.core.database import db_manager
            from backend.core.permissions import set_chip_context
            try:
                with set_chip_context("core"):
                    with db_manager.get_connection() as conn:
                        # Ensure canonical order to avoid duplicate edges if possible, 
                        # but the table treats them as a set via source_id/target_id PK.
                        # We store one direction, load reconstructs bi-directionality.
                        u1, u2 = sorted([node_id_a, node_id_b])
                        conn.execute("INSERT OR IGNORE INTO ai_host_knowledge_edges (source_id, target_id) VALUES (?, ?)", (u1, u2))
                        conn.commit()
            except Exception as e:
                logger.error(f"[KNOWLEDGE_EDGE_ERROR] {e}")

            logger.info(f"[KNOWLEDGE_LINK_CREATED] {node_id_a} <-> {node_id_b}")
            return True
        return False

    def _normalize(self, text: str) -> str:
        import unicodedata
        return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower()

    def search_knowledge(self, query: str) -> List[KnowledgeNode]:
        """
        Keyword-based search with accent normalization and partial word matching.
        """
        q_norm = self._normalize(query)
        # Use first 6 chars as stem for longer words to match variations (e.g., logística -> logísticos)
        q_stems = [w[:6] if len(w) > 6 else w for w in q_norm.split() if len(w) > 2]
        
        results = []
        for node in self.nodes.values():
            n_title = self._normalize(node.title)
            n_desc = self._normalize(node.description)
            n_tags = [self._normalize(t) for t in node.tags]
            
            # Match if full query is in or if any stem matches
            match = (q_norm in n_title or q_norm in n_desc or any(q_norm in t for t in n_tags))
            
            if not match and q_stems:
                # Try stem by stem
                for qs in q_stems:
                    if qs in n_title or qs in n_desc or any(qs in t for t in n_tags):
                        match = True
                        break
            
            if match:
                results.append(node)
        return results

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self.nodes.get(node_id)

    def get_all_nodes(self) -> List[KnowledgeNode]:
        return list(self.nodes.values())

knowledge_graph = KnowledgeGraph()
