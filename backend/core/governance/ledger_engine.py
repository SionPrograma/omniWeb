import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class LedgerEntry(BaseModel):
    ledger_id: str
    decision_type: str
    target_ref_type: str
    target_id: str
    actor: str
    action_taken: str
    rationale: str
    evidence_refs: Dict[str, Any]
    severity_context: str
    outcome_state: str
    active_flag: bool
    superseded_by_id: Optional[str]
    created_at: str

class GovernanceLedgerEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE DECISION LEDGER ENGINE.
    Consolidates high-level strategic decisions into a unified forensic book.
    """

    def record_decision(self, 
                       decision_type: str, 
                       target_ref_type: str, 
                       target_id: str, 
                       actor: str, 
                       action_taken: str, 
                       rationale: str, 
                       evidence_refs: Dict[str, Any], 
                       severity_context: str = "MODERATE") -> str:
        """
        Creates a new entry in the strategic ledger.
        """
        entry_id = f"GL-{uuid.uuid4().hex[:8].upper()}"
        
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Supersede Logic for certain types
                    # If we make a new decision of the same type on the same target, the old one is superseded.
                    types_to_supersede = [
                        "RISK_OVERRIDE", "STRATEGIC_PIVOT", 
                        "BRANCH_CONSOLIDATION", "PREDICTIVE_SIGNAL_DECISION",
                        "ALTERNATIVE_PATH_ACTION", "RELIEF_MISSION_DECISION"
                    ]
                    if decision_type in types_to_supersede:
                        conn.execute("""
                            UPDATE governance_decision_ledger 
                            SET active_flag = 0, superseded_by_id = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE target_id = ? AND decision_type = ? AND active_flag = 1
                        """, (entry_id, target_id, decision_type))

                    # 2. Insert Entry
                    conn.execute("""
                        INSERT INTO governance_decision_ledger (
                            ledger_id, decision_type, target_ref_type, target_id, 
                            actor, action_taken, rationale, evidence_refs, 
                            severity_context, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry_id, decision_type, target_ref_type, target_id,
                        actor, action_taken, rationale, json.dumps(evidence_refs),
                        severity_context, datetime.now().isoformat()
                    ))
                    conn.commit()
                    logger.info(f"Recorded strategic decision {entry_id} ({decision_type})")
                    return entry_id
            except Exception as e:
                logger.error(f"Failed to record ledger entry: {e}")
                return ""

    def update_outcome(self, target_id: str, outcome: str):
        """
        Updates the outcome state for all active decisions related to a target.
        Used when a branch is merged/discarded.
        """
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        UPDATE governance_decision_ledger 
                        SET outcome_state = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE target_id = ? AND active_flag = 1 AND outcome_state = 'PENDING_OUTCOME'
                    """, (outcome, target_id))
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to update ledger outcome: {e}")

    def get_ledger(self, filter_type: Optional[str] = None, target_id: Optional[str] = None) -> List[LedgerEntry]:
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM governance_decision_ledger WHERE 1=1"
                    params = []
                    if filter_type:
                        query += " AND decision_type = ?"
                        params.append(filter_type)
                    if target_id:
                        query += " AND target_id = ?"
                        params.append(target_id)
                    
                    query += " ORDER BY created_at DESC"
                    
                    rows = conn.execute(query, params).fetchall()
                    for r in rows:
                        results.append(LedgerEntry(
                            ledger_id=r["ledger_id"],
                            decision_type=r["decision_type"],
                            target_ref_type=r["target_ref_type"],
                            target_id=r["target_id"],
                            actor=r["actor"],
                            action_taken=r["action_taken"],
                            rationale=r["rationale"],
                            evidence_refs=json.loads(r["evidence_refs"]),
                            severity_context=r["severity_context"],
                            outcome_state=r["outcome_state"],
                            active_flag=bool(r["active_flag"]),
                            superseded_by_id=r["superseded_by_id"],
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch ledger: {e}")
        return results

governance_ledger_engine = GovernanceLedgerEngine()
