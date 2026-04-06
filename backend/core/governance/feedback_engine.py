import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class WisdomFeedbackEngine:
    """
    OMNIWEB — SUBBLOQUE: WISDOM FEEDBACK COMPARISON ENGINE.
    Closes the loop between Wisdom Auto-Drafts and real world outcomes by evaluating
    if the tactical wisdom provided by Atlas was accurate, partially successful or incorrect.
    """
    
    def process_mission_completion(self, mission_id: str, outcome_data: Optional[Dict[str, Any]] = None):
        """
        Triggered when a mission is COMPLETED, FAILED or ARCHIVED.
        Analyzes if wisdom from a source draft was confirmed by reality.
        """
        with db_manager.get_connection() as conn:
            # 1. Identify the draft source of this mission
            # Check if feedback already exists
            existing = conn.execute("SELECT feedback_id FROM governance_wisdom_feedback WHERE resulting_mission_ref = ?", (mission_id,)).fetchone()
            if existing:
                return

            mission_row_raw = conn.execute("SELECT * FROM system_missions WHERE mission_id = ?", (mission_id,)).fetchone()
            
            if not mission_row_raw:
                logger.warning(f"Mission {mission_id} not found in system_missions. Skipping feedback.")
                return

            mission_row = dict(mission_row_raw)
            draft_id = mission_row.get("source_draft_id")
            if not draft_id:
                # Fallback to metadata in parameters (backwards compatibility)
                if mission_row.get("parameters"):
                    try:
                        params = json.loads(mission_row["parameters"])
                        draft_id = params.get("source_draft")
                    except: pass
            
            if not draft_id:
                logger.info(f"Mission {mission_id} has no wisdom draft source. Skipping feedback loop.")
                return

            # 2. Fetch the draft details
            draft_row_raw = conn.execute("SELECT * FROM governance_mission_auto_drafts WHERE draft_id = ?", (draft_id,)).fetchone()
            if not draft_row_raw:
                logger.warning(f"Source draft {draft_id} not found for mission {mission_id}.")
                return
            
            draft_row = dict(draft_row_raw)

            # 3. Augment outcome data if missing
            if not outcome_data:
                outcome_data = self._reconstruct_outcome(conn, mission_row)

            # 4. Generate comparison feedback
            self._generate_feedback(draft_row, mission_row, outcome_data)

    def _reconstruct_outcome(self, conn, mission_row: Any) -> Dict[str, Any]:
        """Heuristic reconstruction of mission outcome from available telemetry and state."""
        mission_id = mission_row["mission_id"]
        status = mission_row["status"]
        
        # Look for existing autopsy if this mission belongs to a branch
        branch_id = mission_row.get("branched_from")
        autopsy = None
        if branch_id:
            autopsy = conn.execute("SELECT * FROM governance_branch_autopsies WHERE branch_id = ?", (branch_id,)).fetchone()
        
        # Calculate completion rate
        completed = json.loads(mission_row["completed_steps"] or "[]")
        pending = json.loads(mission_row["pending_steps"] or "[]")
        total = len(completed) + len(pending)
        completion_ratio = len(completed) / total if total > 0 else 0
        
        outcome_friction = mission_row.get("friction", 1.0) # We added friction column in Phase 113
        
        outcome = {
            "status": status,
            "completion_ratio": completion_ratio,
            "actual_outcome_friction": outcome_friction,
            "preconditions_respected": mission_row.get("preconditions_ok", 1), # Default 1 (respected)
            "autopsy_summary": autopsy["lessons_learned"] if autopsy else None,
            "supporting_refs": {"autopsy_id": autopsy["autopsy_id"]} if autopsy else {}
        }
        
        # Heuristic for success based on status
        outcome["success_score"] = 0.0
        if status == "COMPLETED":
            outcome["success_score"] = 1.0
        elif status == "FAILED":
            outcome["success_score"] = 0.0
        elif status == "SUPERSEDED" or status == "ARCHIVED":
            outcome["success_score"] = completion_ratio
            
        return outcome

    def _generate_feedback(self, draft: Dict[str, Any], mission: Any, outcome: Dict[str, Any]):
        """
        Final Comparison Logic (PHASE 114).
        Classifies comparison into categories and proposes confidence deltas.
        """
        mission_id = mission["mission_id"]
        draft_id = draft["draft_id"]
        
        # Predicted Intent (from Draft)
        predicted_goal = draft["objective_suggestion"]
        
        # Logic for Taxonomy
        fb_state = "INSUFFICIENT_OUTCOME_SIGNAL"
        conf_delta = 0.0
        reuse_delta = 0.0
        rationale = "No hay suficiente señal de resultado para emitir un juicio definitivo."
        actual_summary = f"Estado: {outcome['status']} | Completado: {outcome['completion_ratio']*100:.0f}%"

        # Check preconditions first
        preconditions_ok = outcome.get("preconditions_respected", 1) == 1
        
        if outcome["status"] in ["COMPLETED", "FAILED"] or outcome["completion_ratio"] > 0.5:
            # Case 1: WISDOM_CONFIRMED
            if outcome["status"] == "COMPLETED":
                fb_state = "WISDOM_CONFIRMED"
                conf_delta = 0.05
                reuse_delta = 0.05
                rationale = f"Misión completada siguiendo la táctica sugerida. El nodo Atlas '{draft['source_atlas_node_ref']}' demostró validez operativa."
                actual_summary = "Misión finalizada con éxito según el plan."
            
            # Case 2: WISDOM_CONTRADICTED
            elif outcome["status"] == "FAILED":
                if preconditions_ok:
                    fb_state = "WISDOM_CONTRADICTED"
                    conf_delta = -0.15
                    reuse_delta = -0.10
                    rationale = f"A pesar de seguir las precondiciones, la misión falló. La sabiduría del nodo '{draft['source_atlas_node_ref']}' podría estar obsoleta o no ser aplicable a este contexto técnico."
                    actual_summary = "Fallo técnico catastrófico o bloqueo insalvable siguiendo el draft."
                else:
                    # Case 4: DRAFT_MISAPPLIED
                    fb_state = "DRAFT_MISAPPLIED"
                    conf_delta = 0.0
                    reuse_delta = 0.0
                    rationale = "Las precondiciones críticas fueron ignoradas. El fallo no invalida la sabiduría del nodo, sino su aplicación descuidada."
                    actual_summary = "Misión fallida con precondiciones incumplidas."

            # Case 3: WISDOM_PARTIALLY_CONFIRMED
            elif outcome["completion_ratio"] > 0.5:
                fb_state = "WISDOM_PARTIALLY_CONFIRMED"
                conf_delta = 0.02
                reuse_delta = 0.0
                rationale = "La misión avanzó significativamente pero se detuvo o fue archivada. Se valida la dirección técnica pero no la resolución completa."
                actual_summary = f"Misión interrumpida al {outcome['completion_ratio']*100:.0f}% de ejecución."

        # Filter for "INSUFFICIENT SIGNAL" if mission was cancelled too early
        if outcome["completion_ratio"] < 0.2 and outcome["status"] not in ["COMPLETED", "FAILED"]:
            fb_state = "INSUFFICIENT_OUTCOME_SIGNAL"
            conf_delta = 0.0
            rationale = "La misión fue cancelada o cerrada antes de generar impacto suficiente para evaluar la calidad del draft."

        # Persist Final Feedback
        fb_id = f"FB-W-{uuid.uuid4().hex[:8].upper()}"
        with db_manager.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO governance_wisdom_feedback (
                        feedback_id, source_atlas_node_ref, source_draft_ref, 
                        resulting_mission_ref, resulting_branch_ref,
                        predicted_intent, actual_outcome_summary,
                        preconditions_respected, feedback_state, rationale,
                        supporting_refs, proposed_confidence_delta, proposed_reusability_delta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fb_id, draft["source_atlas_node_ref"], draft_id,
                    mission_id, mission.get("branched_from"),
                    predicted_goal, actual_summary,
                    1 if preconditions_ok else 0, fb_state, rationale,
                    json.dumps(outcome.get("supporting_refs", {})),
                    conf_delta, reuse_delta
                ))
                conn.commit()
                logger.info(f"[WISDOM_FEEDBACK] Loop closed for {mission_id}: {fb_state} ({fb_id})")
            except Exception as e:
                logger.error(f"Failed to persist wisdom feedback: {e}")

    def apply_feedback(self, feedback_id: str) -> bool:
        """
        Manually trigger the recalibration of the Atlas node based on feedback.
        (Called only after Creator approval in subsequent units).
        """
        with db_manager.get_connection() as conn:
            fb = conn.execute("SELECT * FROM governance_wisdom_feedback WHERE feedback_id = ?", (feedback_id,)).fetchone()
            if not fb or fb["creator_decision"] != 'PENDING':
                return False
            
            node_ref = fb["source_atlas_node_ref"]
            
            # Apply to learning items (Atlas nodes)
            # Standard IDs are like 'WNODE-L-id' or 'WNODE-A-id'
            table_name = "governance_learning_items"
            id_col = "learning_item_id"
            target_id = node_ref
            
            if node_ref.startswith("WNODE-L-"):
                target_id = node_ref.replace("WNODE-L-", "")
            elif node_ref.startswith("WNODE-A-"):
                table_name = "governance_wisdom_atlas"
                id_col = "node_id"
                target_id = node_ref.replace("WNODE-A-", "")

            try:
                conn.execute(f"""
                    UPDATE {table_name} 
                    SET confidence = MIN(1.0, MAX(0.1, confidence + ?))
                    WHERE {id_col} = ?
                """, (fb["proposed_confidence_delta"], target_id))
                
                # Update reusability if column exists (optional for now)
                # ...
                
                conn.execute("UPDATE governance_wisdom_feedback SET creator_decision = 'APPLIED' WHERE feedback_id = ?", (feedback_id,))
                conn.commit()
                logger.info(f"[FEEDBACK_APPLIED] Node {node_ref} recalibrated by {fb['proposed_confidence_delta']:.2f}")
                return True
            except Exception as e:
                logger.error(f"Recalibration failed for node {node_ref}: {e}")
                return False

    def reject_feedback(self, feedback_id: str) -> bool:
        """Marks a wisdom feedback as IGNORED/REJECTED without applying it."""
        with db_manager.get_connection() as conn:
            fb = conn.execute("SELECT * FROM governance_wisdom_feedback WHERE feedback_id = ?", (feedback_id,)).fetchone()
            if not fb or fb["creator_decision"] != 'PENDING':
                return False
            
            conn.execute("UPDATE governance_wisdom_feedback SET creator_decision = 'REJECTED' WHERE feedback_id = ?", (feedback_id,))
            conn.commit()
            return True

wisdom_feedback_engine = WisdomFeedbackEngine()
