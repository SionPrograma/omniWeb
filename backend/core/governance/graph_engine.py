import logging
import json
import uuid
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.governance.atlas_engine import AtlasNode

logger = logging.getLogger(__name__)

class WisdomGraphEngine:
    """
    OMNIWEB — BLOQUE: WISDOM GRAPH EXPLORER ENGINE.
    Builds and manages the hierarchical relationships between tactical wisdom nodes.
    """
    def __init__(self):
        self.default_project = "PROJECT_OMNIWEB_PROD"

    def rebuild_graph(self):
        """Discovers and persists all justifiable relations between atlas nodes."""
        with set_chip_context("core"):
            try:
                self._clear_edges()
                self._discover_replay_relations()
                self._discover_autopsy_derivations()
                self._discover_ledger_impacts()
                self._discover_contextual_matches()
                self._discover_domain_clusters()
                logger.info("Wisdom Graph rebuilt successfully.")
            except Exception as e:
                logger.error(f"Failed to rebuild wisdom graph: {e}")

    def _clear_edges(self):
        """Resets the graph edges before discovery."""
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM governance_wisdom_graph_edges")
            conn.commit()

    def _discover_replay_relations(self):
        """Connects Replay Syncs to Autopsies and Learnings."""
        with db_manager.get_connection() as conn:
            # 1. Sync -> Autopsy (CONFIRMED_BY / CONTRADICTED_BY)
            rows = conn.execute("SELECT * FROM governance_replay_syncs").fetchall()
            for r in rows:
                source_id = f"WNODE-SYN-{r['sync_id'][:8]}"
                target_autopsy_id = f"WNODE-AUT-{r['autopsy_id'][:8]}"
                rel_type = "CONFIRMED_BY" if r["replay_outcome_state"] == "SIMULATION_CONFIRMED" else "CONTRADICTED_BY"
                
                self._upsert_edge(source_id, target_autopsy_id, rel_type, 1.0, r["rationale"])

                # 2. Sync -> Learning (VALIDATES_TACTIC)
                sim_res = conn.execute("SELECT source_object_id FROM governance_tactical_simulations WHERE simulation_id = ?", (r["simulation_id"],)).fetchone()
                if sim_res:
                    target_learning_id = f"WNODE-{sim_res['source_object_id'][:8]}"
                    self._upsert_edge(source_id, target_learning_id, "VALIDATES_TACTIC", 0.9, "Validación de la táctica simulada.")

    def _discover_autopsy_derivations(self):
        """Connects Autopsies to the Learnings that were born from them."""
        # Note: In OmniWeb, learnings are often extracted from autopsies.
        # We assume for now they share a project and domain, or were created near the same time.
        # In a more advanced version, we'd have a specific learning_source_id field.
        pass

    def _discover_ledger_impacts(self):
        """Connects Strategic Decisions to the nodes that provided evidence."""
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_decision_ledger WHERE active_flag = 1").fetchall()
            for r in rows:
                source_id = f"WNODE-DEC-{r['ledger_id'][:8]}"
                # If target_id is a branch, find its autopsy and relate it.
                if r["target_ref_type"] == "BRANCH":
                    aut_res = conn.execute("SELECT autopsy_id FROM governance_branch_autopsies WHERE branch_id = ?", (r["target_id"],)).fetchone()
                    if aut_res:
                        target_id = f"WNODE-AUT-{aut_res['autopsy_id'][:8]}"
                        self._upsert_edge(source_id, target_id, "TRIGGERED_BY", 0.8, "Decisión basada en hallazgos de autopsia.")

    def _discover_contextual_matches(self):
        """Connects Context Mappings to their source projects and related learnings."""
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_contextual_mappings WHERE status = 'APPLIED'").fetchall()
            for r in rows:
                source_id = f"WNODE-MAP-{r['mapping_id'][:8]}"
                # No project node yet in Atlas, but we can link to nodes within that project.
                # Find nodes in source_project.
                source_nodes = conn.execute("SELECT node_id FROM governance_wisdom_atlas_nodes WHERE project_id = ? LIMIT 5", (r["source_project_id"],)).fetchall()
                for sn in source_nodes:
                    self._upsert_edge(source_id, sn["node_id"], "BASELINE_SOURCE", 0.7, f"Proveniente de proyecto: {r['source_project_id']}")

    def _discover_domain_clusters(self):
        """Connects nodes that share high-confidence domain knowledge."""
        # Cluster-level grouping to show central hubs.
        with db_manager.get_connection() as conn:
            # Connect high-confidence learnings within the same domain.
            rows = conn.execute("""
                SELECT node_id, affected_domains, confidence 
                FROM governance_wisdom_atlas_nodes 
                WHERE confidence > 0.8 AND node_type = 'LEARNING'
            """).fetchall()
            
            # Simple N^2 for discovery in small datasets, in production use better indexing.
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    d1 = json.loads(rows[i]["affected_domains"])
                    d2 = json.loads(rows[j]["affected_domains"])
                    shared = set(d1).intersection(set(d2))
                    if shared:
                        self._upsert_edge(rows[i]["node_id"], rows[j]["node_id"], "RELATED_DOMAIN", 0.5, f"Comparten dominio: {list(shared)[0]}")

    def _upsert_edge(self, source_id: str, target_id: str, rel_type: str, strength: float, rationale: str):
        """Persists a graph edge."""
        edge_id = f"WEDGE-{uuid.uuid4().hex[:8]}"
        with db_manager.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO governance_wisdom_graph_edges (
                        edge_id, source_node_id, target_node_id, relation_type, strength, rationale
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_node_id, target_node_id, relation_type) DO UPDATE SET
                        strength = excluded.strength,
                        rationale = excluded.rationale
                """, (edge_id, source_id, target_id, rel_type, strength, rationale))
                conn.commit()
            except sqlite3.OperationalError: pass # Handle cases where one node might not exist

    def get_graph_data(self) -> Dict[str, Any]:
        """Returns nodes and edges prepared for frontend visualization."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Fetch Edges
                edges = []
                edge_rows = conn.execute("SELECT * FROM governance_wisdom_graph_edges").fetchall()
                
                # Active nodes mentioned in edges
                active_node_ids = set()
                for r in edge_rows:
                    edges.append({
                        "id": r["edge_id"],
                        "source": r["source_node_id"],
                        "target": r["target_node_id"],
                        "type": r["relation_type"],
                        "strength": r["strength"],
                        "rationale": r["rationale"]
                    })
                    active_node_ids.add(r["source_node_id"])
                    active_node_ids.add(r["target_node_id"])

                # 2. Fetch Nodes (only those connected or top ones if graph is empty)
                nodes = []
                if not active_node_ids:
                    node_rows = conn.execute("SELECT * FROM governance_wisdom_atlas_nodes ORDER BY reusability_score DESC LIMIT 20").fetchall()
                else:
                    placeholders = ",".join(["?" for _ in active_node_ids])
                    node_rows = conn.execute(f"SELECT * FROM governance_wisdom_atlas_nodes WHERE node_id IN ({placeholders})", list(active_node_ids)).fetchall()
                
                for r in node_rows:
                    nodes.append({
                        "id": r["node_id"],
                        "type": r["node_type"],
                        "title": r["title"],
                        "confidence": r["confidence"],
                        "reusability": r["reusability_score"],
                        "status": r["status_band"],
                        "project": r["project_id"]
                    })

                return {"nodes": nodes, "links": edges}

graph_engine = WisdomGraphEngine()
