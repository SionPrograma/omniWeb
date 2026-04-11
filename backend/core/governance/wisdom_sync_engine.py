import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class WisdomSyncEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE POST-MISSION WISDOM SYNC.
    Closes the strategic loop by evaluating real results vs wisdom suggestions.
    """
    
    def __init__(self):
        self.classifications = {
            "CONFIRMED": "WISDOM_CONFIRMED",
            "PARTIAL": "WISDOM_PARTIAL",
            "CONTRADICTED": "WISDOM_CONTRADICTED",
            "UNKNOWN": "WISDOM_INSUFFICIENT_EVIDENCE"
        }

    def evaluate_mission_outcome(self, mission_id: str) -> Optional[str]:
        """
        Evaluates a mission autopsy and mission draft metadata to generate a wisdom sync proposal.
        """
        try:
            with db_manager.get_connection() as conn:
                # 1. Get Mission and Draft info
                mission = conn.execute("""
                    SELECT m.mission_id, m.mission_status, d.source_atlas_node_ref, d.catalyst_trace_id, d.confidence
                    FROM system_missions m
                    JOIN governance_mission_auto_drafts d ON m.source_draft_id = d.draft_id
                    WHERE m.mission_id = ?
                """, (mission_id,)).fetchone()
                
                if not mission or not mission["source_atlas_node_ref"]:
                    return None
                
                node_id = mission["source_atlas_node_ref"]
                status = mission["mission_status"]
                
                # 2. Classification Logic
                classification = self.classifications["UNKNOWN"]
                conf_delta = 0.0
                summary = "Resultado de ejecución por defecto."
                
                if status == 'COMPLETED':
                    classification = self.classifications["CONFIRMED"]
                    conf_delta = 0.05
                    summary = "La misión se completó con éxito, validando la sabiduría táctica sugerida."
                elif status == 'PARTIAL':
                    classification = self.classifications["PARTIAL"]
                    conf_delta = 0.01
                    summary = "La misión logró objetivos parciales; la sabiduría es útil pero incompleta."
                elif status == 'FAILED':
                    classification = self.classifications["CONTRADICTED"]
                    conf_delta = -0.10
                    summary = "La misión falló. La sabiduría original podría ser obsoleta o errónea en este dominio."
                
                # 3. Create Proposal
                proposal_id = f"SYNC-{uuid.uuid4().hex[:8].upper()}"
                conn.execute("""
                    INSERT INTO governance_wisdom_sync_proposals (
                        proposal_id, source_wisdom_node_id, source_mission_id, catalyst_trace_id,
                        outcome_classification, evidence_summary, confidence_delta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal_id, node_id, mission_id, mission["catalyst_trace_id"],
                    classification, summary, conf_delta
                ))
                conn.commit()
                return proposal_id
                
        except Exception as e:
            logger.error(f"Wisdom Sync Evaluation failed for {mission_id}: {e}")
            return None

    def approve_sync_proposal(self, proposal_id: str) -> bool:
        """
        Applies a wisdom sync proposal: updates the Atlas node confidence.
        """
        try:
            with db_manager.get_connection() as conn:
                proposal = conn.execute("""
                    SELECT source_wisdom_node_id, confidence_delta 
                    FROM governance_wisdom_sync_proposals 
                    WHERE proposal_id = ? AND status = 'PENDING_REVIEW'
                """, (proposal_id,)).fetchone()
                
                if not proposal:
                    return False
                
                # Update Node Confidence in Atlas
                conn.execute("""
                    UPDATE governance_wisdom_atlas_nodes 
                    SET confidence = MIN(1.0, MAX(0.0, confidence + ?))
                    WHERE node_id = ?
                """, (proposal["confidence_delta"], proposal["source_wisdom_node_id"]))
                
                # Close Proposal
                conn.execute("""
                    UPDATE governance_wisdom_sync_proposals 
                    SET status = 'APPROVED' 
                    WHERE proposal_id = ?
                """, (proposal_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to approve sync proposal {proposal_id}: {e}")
            return False

wisdom_sync_engine = WisdomSyncEngine()
