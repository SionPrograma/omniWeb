import logging
import json
import uuid
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class AtlasNode(BaseModel):
    node_id: str
    node_type: str
    source_ref_type: Optional[str] = None
    source_ref_id: Optional[str] = None
    project_id: Optional[str] = "PROJECT_OMNIWEB_PROD"
    affected_domains: List[str] = []
    title: str
    summary: str
    confidence: float = 0.5
    reusability_score: float = 0.5
    status_band: str = "EXPERIMENTAL"
    related_refs: List[str] = []
    evidence_refs: Dict[str, Any] = {}
    freshness: float = 1.0
    created_at: str = datetime.now().isoformat()
    updated_at: str = datetime.now().isoformat()

class AtlasAggregationEngine:
    """
    OMNIWEB — BLOQUE: ATLAS AGGREGATION ENGINE.
    Collects, normalizes, and prioritizes tactical wisdom from various sources.
    """
    def __init__(self):
        self.default_project = "PROJECT_OMNIWEB_PROD"

    def aggregate_all(self):
        """Triggers aggregation from all wisdom sources."""
        with set_chip_context("core"):
            try:
                self._aggregate_learnings()
                self._aggregate_autopsies()
                self._aggregate_decisions()
                self._aggregate_replay_syncs()
                self._aggregate_context_mappings()
                logger.info("Wisdom Atlas aggregation completed.")
            except Exception as e:
                logger.error(f"Failed to aggregate wisdom atlas: {e}")


    def _aggregate_learnings(self):
        """Converts Learning Items into Atlas Nodes."""
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_learning_items").fetchall()
            for row in rows:
                r = dict(row)
                node = AtlasNode(
                    node_id=f"WNODE-{(r['learning_item_id'] or 'unknown')[:8]}",
                    node_type="LEARNING",
                    source_ref_type="governance_learning_items",
                    source_ref_id=r["learning_item_id"],
                    project_id=r.get("project_id", self.default_project),
                    affected_domains=[r.get("target_domain", "global")],
                    title=f"Lección: {(r.get('lesson_summary') or '')[:50]}...",
                    summary=r.get("lesson_summary") or "Sin resumen.",
                    confidence=r.get("confidence") if r.get("confidence") is not None else 0.5,
                    reusability_score=0.8 if not r.get("is_antipattern") else 0.4,
                    status_band="CONFIRMED" if (r.get("occurrence_count") or 0) > 1 else "EXPERIMENTAL",
                    evidence_refs={"behavior": r.get("recommended_behavior"), "occurrences": r.get("occurrence_count") or 0},
                    created_at=r.get("created_at") if r.get("created_at") else datetime.now().isoformat()
                )
                self._upsert_node(node)

    def _aggregate_autopsies(self):
        """Converts forensic autopsies into Atlas Nodes."""
        with db_manager.get_connection() as conn:
            try:
                rows = conn.execute("SELECT * FROM governance_branch_autopsies").fetchall()
            except sqlite3.OperationalError: 
                return 

            for row in rows:
                r = dict(row)
                status = "CONFIRMED" if r.get("final_branch_outcome") == "MERGED" else "EXPERIMENTAL"
                sync_check = conn.execute("SELECT replay_outcome_state FROM governance_replay_syncs WHERE autopsy_id = ? LIMIT 1", (r["autopsy_id"],)).fetchone()
                if sync_check and sync_check["replay_outcome_state"] == "CONTRADICTED_BY_REALITY":
                    status = "CONTRADICTED_BY_REALITY"

                node = AtlasNode(
                    node_id=f"WNODE-AUT-{(r['autopsy_id'] or 'unknown')[:8]}",
                    node_type="AUTOPSY",
                    source_ref_type="governance_branch_autopsies",
                    source_ref_id=r["autopsy_id"],
                    project_id=self.default_project,
                    affected_domains=json.loads(r["affected_domains"]) if r.get("affected_domains") else [],
                    title=f"Autopsia: {(r.get('branch_goal_summary') or '')[:50]}...",
                    summary=r.get("structural_findings") or "Sin hallazgos estructurales detallados.",
                    confidence=r.get("confidence") if r.get("confidence") is not None else 0.5,
                    reusability_score=0.7, 
                    status_band=status,
                    evidence_refs={"outcome": r.get("final_branch_outcome"), "hotspots": r.get("hotspot_history")},
                    created_at=r.get("created_at") if r.get("created_at") else datetime.now().isoformat()
                )
                self._upsert_node(node)

    def _aggregate_decisions(self):
        """Converts key decisions (Patterns) from Ledger into Atlas Nodes."""
        with db_manager.get_connection() as conn:
            try:
                rows = conn.execute("""
                    SELECT * FROM governance_decision_ledger 
                    WHERE decision_type IN ('RISK_OVERRIDE', 'STRATEGIC_PIVOT', 'BRANCH_CONSOLIDATION')
                    AND active_flag = 1
                """).fetchall()
            except sqlite3.OperationalError: return

            for row in rows:
                r = dict(row)
                node = AtlasNode(
                    node_id=f"WNODE-DEC-{(r['ledger_id'] or 'unknown')[:8]}",
                    node_type="DECISION",
                    source_ref_type="governance_decision_ledger",
                    source_ref_id=r["ledger_id"],
                    project_id=self.default_project,
                    affected_domains=[r["target_id"]] if r.get("target_ref_type") == "DOMAIN" else [],
                    title=f"Decisión: {r.get('decision_type', 'UNKNOWN')} - {r.get('action_taken', 'TAKEN')}",
                    summary=r.get("rationale") or "Sin resumen de decisión.",
                    confidence=1.0,
                    reusability_score=0.3, 
                    status_band="CONFIRMED",
                    evidence_refs={"actor": r["actor"], "severity": r["severity_context"]},
                    created_at=r["created_at"]
                )
                self._upsert_node(node)

    def _aggregate_replay_syncs(self):
        """Converts Replay Syncs into validation nodes."""
        with db_manager.get_connection() as conn:
            try:
                rows = conn.execute("SELECT * FROM governance_replay_syncs").fetchall()
            except sqlite3.OperationalError: return

            for row in rows:
                r = dict(row)
                node = AtlasNode(
                    node_id=f"WNODE-SYN-{(r['sync_id'] or 'unknown')[:8]}",
                    node_type="REPLAY_SYNC",
                    source_ref_type="governance_replay_syncs",
                    source_ref_id=r["sync_id"],
                    project_id=self.default_project,
                    affected_domains=[], 
                    title=f"Validación: {r.get('replay_outcome_state', 'SYNCED')}",
                    summary=r.get("rationale") or "Sin resumen de validación.",
                    confidence=0.9,
                    reusability_score=0.9,
                    status_band=r.get("replay_outcome_state") or "SYNCED",
                    evidence_refs={"predicted": r.get("predicted_effect"), "actual": r.get("actual_outcome_summary")},
                    created_at=datetime.now().isoformat()
                )
                self._upsert_node(node)

    def _aggregate_context_mappings(self):
        """Converts similarity mappings into nodes."""
        with db_manager.get_connection() as conn:
            try:
                rows = conn.execute("SELECT * FROM governance_contextual_mappings").fetchall()
            except sqlite3.OperationalError: return

            for row in rows:
                r = dict(row)
                node = AtlasNode(
                    node_id=f"WNODE-MAP-{r['mapping_id'][:8]}",
                    node_type="CONTEXT_MAPPING",
                    source_ref_type="governance_contextual_mappings",
                    source_ref_id=r["mapping_id"],
                    project_id=r["target_project_id"],
                    affected_domains=[],
                    title=f"Mapeo: {r.get('source_project_id') or 'SRC'} -> {r.get('target_project_id') or 'TGT'}",
                    summary=r.get("rationale") or "Sin resumen de mapeo.",
                    confidence=r.get("similarity_score") if r.get("similarity_score") is not None else 0.5,
                    reusability_score=(r["similarity_score"] if "similarity_score" in r.keys() else 0.5) * 0.8,
                    status_band="CONFIRMED" if r["status"] == "APPLIED" else "EXPERIMENTAL",
                    evidence_refs={"source_project": r["source_project_id"], "similarity": r["similarity_score"]},
                    created_at=r["created_at"]
                )
                self._upsert_node(node)

    def _upsert_node(self, node: AtlasNode):
        """Inserts or updates a node in the atlas table."""
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO governance_wisdom_atlas_nodes (
                    node_id, node_type, source_ref_type, source_ref_id, 
                    project_id, affected_domains, title, summary, 
                    confidence, reusability_score, status_band, 
                    related_refs, evidence_refs, freshness, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET
                    title = excluded.title,
                    summary = excluded.summary,
                    confidence = excluded.confidence,
                    reusability_score = excluded.reusability_score,
                    status_band = excluded.status_band,
                    evidence_refs = excluded.evidence_refs,
                    updated_at = excluded.updated_at
            """, (
                node.node_id, node.node_type, node.source_ref_type, node.source_ref_id,
                node.project_id, json.dumps(node.affected_domains), node.title, node.summary,
                node.confidence, node.reusability_score, node.status_band,
                json.dumps(node.related_refs), json.dumps(node.evidence_refs),
                node.freshness, node.created_at, datetime.now().isoformat()
            ))
            conn.commit()

    def get_nodes(self, node_type: Optional[str] = None, project_id: Optional[str] = None) -> List[AtlasNode]:
        """Fetches nodes from the atlas."""
        results = []
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                query = "SELECT * FROM governance_wisdom_atlas_nodes WHERE 1=1"
                params = []
                if node_type:
                    query += " AND node_type = ?"
                    params.append(node_type)
                if project_id:
                    query += " AND project_id = ?"
                    params.append(project_id)
                
                query += " ORDER BY reusability_score DESC, confidence DESC"
                
                rows = conn.execute(query, params).fetchall()
                for r in rows:
                    results.append(AtlasNode(
                        node_id=r["node_id"],
                        node_type=r["node_type"],
                        source_ref_type=r["source_ref_type"],
                        source_ref_id=r["source_ref_id"],
                        project_id=r["project_id"],
                        affected_domains=json.loads(r["affected_domains"]),
                        title=r["title"],
                        summary=r["summary"],
                        confidence=r["confidence"],
                        reusability_score=r["reusability_score"],
                        status_band=r["status_band"],
                        related_refs=json.loads(r["related_refs"]),
                        evidence_refs=json.loads(r["evidence_refs"]),
                        freshness=r["freshness"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"]
                    ))
        return results

    def get_node_sync_history(self, node_id: str) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: ATLAS EVIDENCE UI.
        Retrieves all post-mission sync entries linked to a specific node_id
        and provides a summary of outcomes.
        """
        history = []
        summary = {
            "WISDOM_CONFIRMED": 0,
            "WISDOM_PARTIAL": 0,
            "WISDOM_CONTRADICTED": 0,
            "EXECUTION_BIASED": 0,
            "INSUFFICIENT_SIGNAL": 0,
            "total_syncs": 0,
            "last_reviewed_at": None
        }
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Searching node_id inside JSON list via LIKE
                rows = conn.execute("SELECT * FROM governance_post_mission_syncs WHERE source_atlas_node_ids LIKE ? ORDER BY created_at DESC", (f'%"{node_id}"%',)).fetchall()
                for r in rows:
                    rd = dict(r)
                    history.append(rd)
                    outcome = rd.get("actual_outcome_type")
                    if outcome in summary:
                        summary[outcome] += 1
                        summary["total_syncs"] += 1
                    
                    if rd.get("is_applied") and (not summary["last_reviewed_at"] or rd["created_at"] > summary["last_reviewed_at"]):
                        summary["last_reviewed_at"] = rd["created_at"]
                        
        return {"history": history, "summary": summary}

atlas_engine = AtlasAggregationEngine()
