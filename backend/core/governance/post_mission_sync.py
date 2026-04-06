import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from datetime import datetime

logger = logging.getLogger(__name__)

class PostMissionWisdomSyncEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE POST-MISSION WISDOM SYNC.
    Closes the loop between REAL outcome and the Wisdom Atlas.
    """
    
    def __init__(self):
        self.outcome_types = {
             "WISDOM_CONFIRMED": {"conf_delta": 0.05, "reuse_delta": 0.03},
             "WISDOM_PARTIAL": {"conf_delta": 0.02, "reuse_delta": 0.01},
             "WISDOM_CONTRADICTED": {"conf_delta": -0.15, "reuse_delta": -0.10},
             "EXECUTION_BIASED": {"conf_delta": 0.0, "reuse_delta": 0.0}, # No blame on wisdom if execution failed
             "INSUFFICIENT_SIGNAL": {"conf_delta": 0.0, "reuse_delta": 0.0}
        }

    def scan_for_closures(self) -> List[Dict[str, Any]]:
        """
        Identifies realized missions that just finished.
        """
        new_proposals = []
        with db_manager.get_connection() as conn:
            # Identificar el proyecto actual para trazabilidad cross-contexto
            curr = conn.execute("SELECT project_id FROM governance_projects WHERE is_current = 1 LIMIT 1").fetchone()
            curr_project = curr["project_id"] if curr else "PROJECT_UNKNOWN"

            # Join Action Packages with Missions
            pending_missions = conn.execute("""
                SELECT m.*, p.package_id, p.involved_nodes_json 
                FROM system_missions m
                JOIN governance_action_packages p ON m.mission_id = p.realized_mission_id
                WHERE (m.status = 'completed' OR m.status = 'failed')
                AND m.mission_id NOT IN (SELECT source_mission_id FROM governance_post_mission_syncs)
            """).fetchall()
            
            for m in pending_missions:
                # Map column name for evaluate_outcome
                m_dict = dict(m)
                m_dict["source_node_ids"] = m_dict.pop("involved_nodes_json")
                m_dict["found_project_id"] = curr_project # Attach context diversity
                proposal = self._evaluate_outcome(m_dict)
                new_proposals.append(proposal)

        self._persist_proposals(new_proposals)
        return new_proposals

    def _evaluate_outcome(self, m: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic to determine if the wisdom was correct.
        friction (1to0): lower means better.
        """
        friction = m.get("friction", 1.0)
        preconds = m.get("preconditions_ok", 1)
        status = m.get("status")

        outcome = "INSUFFICIENT_SIGNAL"
        rationale = f"Misión finalizada con estado {status}."

        if status == 'completed':
            if preconds == 1:
                if friction < 0.3:
                    outcome = "WISDOM_CONFIRMED"
                    rationale = f"Alivio sustancial detectado (Friction: {friction:.2f}). La táctica funcionó como se esperaba."
                elif friction < 0.6:
                    outcome = "WISDOM_PARTIAL"
                    rationale = f"Alivio moderado detectado (Friction: {friction:.2f})."
                else:
                    outcome = "WISDOM_CONTRADICTED"
                    rationale = f"Misión completada pero la fricción sigue alta ({friction:.2f}). La sabiduría origen podría estar desfasada o ser incorrecta para este contexto."
            else:
                outcome = "EXECUTION_BIASED"
                rationale = "Execution failed preconditions. Wisdom cannot be judged fairly."
        else: # failed
             # If it failed but it wasn't due to preconds, maybe the wisdom was too risky?
             outcome = "INSUFFICIENT_SIGNAL"
             rationale = "Misión fallida. Causa incierta."

        deltas = self.outcome_types.get(outcome, {"conf_delta": 0, "reuse_delta": 0})

        return {
            "sync_id": f"SYNC-{uuid.uuid4().hex[:8].upper()}",
            "source_package_id": m["package_id"],
            "source_mission_id": m["mission_id"],
            "source_atlas_node_ids": m["source_node_ids"],
            "actual_outcome_type": outcome,
            "preconditions_respected": True if preconds == 1 else False,
            "execution_context_quality": 1.0 if preconds == 1 else 0.4,
            "proposed_confidence_delta": deltas["conf_delta"],
            "proposed_reusability_delta": deltas["reuse_delta"],
            "rationale": rationale,
            "project_id": m.get("found_project_id", "PROJECT_UNKNOWN"),
            "supporting_evidence": json.dumps({"friction_end": friction})
        }

    def _persist_proposals(self, proposals: List[Dict[str, Any]]):
        if not proposals: return
        with db_manager.get_connection() as conn:
            for p in proposals:
                conn.execute("""
                    INSERT INTO governance_post_mission_syncs (
                        sync_id, source_package_id, source_mission_id, source_atlas_node_ids,
                        actual_outcome_type, preconditions_respected, execution_context_quality,
                        proposed_confidence_delta, proposed_reusability_delta, rationale, supporting_evidence,
                        project_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["sync_id"], p["source_package_id"], p["source_mission_id"], p["source_atlas_node_ids"],
                    p["actual_outcome_type"], p["preconditions_respected"], p["execution_context_quality"],
                    p["proposed_confidence_delta"], p["proposed_reusability_delta"], p["rationale"], p["supporting_evidence"],
                    p["project_id"]
                ))
            conn.commit()

    def apply_sync(self, sync_id: str) -> bool:
        """
        Creator-approved: Updates the actual Atlas nodes.
        """
        with db_manager.get_connection() as conn:
            sync = conn.execute("SELECT * FROM governance_post_mission_syncs WHERE sync_id = ?", (sync_id,)).fetchone()
            if not sync or sync["is_applied"]: return False
            
            node_ids = json.loads(sync["source_atlas_node_ids"])
            c_delta = sync["proposed_confidence_delta"]
            r_delta = sync["proposed_reusability_delta"]
            
            for nid in node_ids:
                # Actualizar confianza y reusabilidad del nodo
                conn.execute("""
                    UPDATE governance_wisdom_atlas_nodes 
                    SET confidence = confidence + ?, reusability_score = reusability_score + ?, 
                        updated_at = CURRENT_TIMESTAMP 
                    WHERE node_id = ?
                """, (c_delta, r_delta, nid))
                
            conn.execute("UPDATE governance_post_mission_syncs SET creator_decision = 'ACCEPTED', is_applied = 1 WHERE sync_id = ?", (sync_id,))
            conn.commit()
            return True

    def get_pending_syncs(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_post_mission_syncs WHERE creator_decision = 'PENDING'").fetchall()
            return [dict(r) for r in rows]

post_mission_sync_engine = PostMissionWisdomSyncEngine()
