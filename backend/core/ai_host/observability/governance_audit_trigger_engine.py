import logging
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class RootCauseAuditProposal(BaseModel):
    audit_id: str
    source_heatmap_node: str
    source_relief_ids: List[str]
    trigger_state: str # READY, POSSIBLE, NEED_OBSERVATION
    confidence: float
    structural_resistance_score: float
    repeated_failure_count: int
    proposed_objective: str
    proposed_scope: str
    rationale: str
    status: str = "PENDING"
    associated_handoff_id: Optional[str] = None
    created_at: str

class GovernanceAuditTriggerEngine:
    """
    OMNIWEB — BLOQUE: FORENSIC ROOT CAUSE AUDIT TRIGGER.
    Detects when a resistant hotspot requires a deep structural audit instead of tactics.
    """

    def scan_for_audit_needs(self) -> List[RootCauseAuditProposal]:
        """
        Scans domains with high structural resistance and generates audit proposals.
        """
        proposals = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Identify domains with RESISTANT_HOTSPOT or ESCALATING outcomes
                    resistant_rows = conn.execute("""
                        SELECT source_heatmap_node, COUNT(*) as fail_count, 
                               GROUP_CONCAT(proposal_id) as relief_ids,
                               MAX(baseline_friction_score) as max_baseline
                        FROM governance_relief_proposals 
                        WHERE relief_outcome IN ('RESISTANT_HOTSPOT', 'ESCALATING_DESPITE_RELIEF', 'RELIEF_INEFFECTIVE')
                        GROUP BY source_heatmap_node
                    """).fetchall()

                    for row in resistant_rows:
                        domain = row["source_heatmap_node"]
                        fail_count = row["fail_count"]
                        relief_ids = row["relief_ids"].split(",") if row["relief_ids"] else []
                        
                        # Check if an audit proposal already exists for this domain
                        existing = conn.execute(
                            "SELECT audit_id FROM governance_root_audit_proposals WHERE source_heatmap_node = ? AND status IN ('PENDING', 'ACCEPTED')",
                            (domain,)
                        ).fetchone()
                        
                        if existing:
                            continue

                        # Trigger Criterias
                        trigger_state = "NEED_OBSERVATION"
                        confidence = 0.5
                        
                        if fail_count >= 2:
                            trigger_state = "ROOT_CAUSE_AUDIT_READY"
                            confidence = 0.85
                        elif fail_count == 1:
                            trigger_state = "ROOT_CAUSE_AUDIT_POSSIBLE"
                            confidence = 0.65

                        if trigger_state != "NEED_OBSERVATION":
                            audit_proposal = self._design_audit(domain, fail_count, relief_ids, trigger_state, confidence)
                            self._persist_audit_proposal(conn, audit_proposal)
                            proposals.append(audit_proposal)

            except Exception as e:
                logger.error(f"Audit trigger scan failed: {e}")
                import traceback
                logger.error(traceback.format_exc())

        return proposals

    def get_proposals(self, domain: Optional[str] = None) -> List[RootCauseAuditProposal]:
        """Returns active audit proposals."""
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM governance_root_audit_proposals WHERE status IN ('PENDING', 'ACCEPTED')"
                    params = []
                    if domain:
                        query += " AND source_heatmap_node = ?"
                        params.append(domain)
                    
                    rows = conn.execute(query, params).fetchall()
                    for r in rows:
                        results.append(RootCauseAuditProposal(
                            audit_id=r["audit_id"],
                            source_heatmap_node=r["source_heatmap_node"],
                            source_relief_ids=r["source_relief_ids"].split(",") if r["source_relief_ids"] else [],
                            trigger_state=r["trigger_state"],
                            confidence=r["confidence"],
                            structural_resistance_score=r["structural_resistance_score"],
                            repeated_failure_count=r["repeated_failure_count"],
                            proposed_objective=r["proposed_objective"],
                            proposed_scope=r["proposed_scope"],
                            rationale=r["rationale"],
                            status=r["status"],
                            associated_handoff_id=r["associated_handoff_id"],
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch audit proposals: {e}")
        return results

    def process_decision(self, audit_id: str, decision: str) -> Dict[str, Any]:
        """Handles Creator's decision (ACCEPT, REJECT, POSTPONE)."""
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    row = conn.execute("SELECT * FROM governance_root_audit_proposals WHERE audit_id = ?", (audit_id,)).fetchone()
                    if not row: return {"status": "error", "message": "Audit proposal not found"}
                    
                    new_status = 'PENDING'
                    handoff_id = None
                    if decision == 'ACCEPT':
                        new_status = 'ACCEPTED'
                        handoff_id = str(uuid.uuid4())
                        # In production this would create a mission in the roadmap
                    elif decision == 'REJECT':
                        new_status = 'REJECTED'
                    elif decision == 'POSTPONE':
                        new_status = 'POSTPONED'
                    
                    conn.execute(
                        "UPDATE governance_root_audit_proposals SET status = ?, associated_handoff_id = ?, updated_at = ? WHERE audit_id = ?",
                        (new_status, handoff_id, datetime.now().isoformat(), audit_id)
                    )
                    conn.commit()
                    return {"status": "success", "decision": decision, "handoff_id": handoff_id}
            except Exception as e:
                logger.error(f"Failed to process audit decision: {e}")
                return {"status": "error", "message": str(e)}

    def _design_audit(self, domain: str, fail_count: int, relief_ids: List[str], state: str, conf: float) -> RootCauseAuditProposal:
        """Designs the audit parameters."""
        return RootCauseAuditProposal(
            audit_id=str(uuid.uuid4()),
            source_heatmap_node=domain,
            source_relief_ids=relief_ids,
            trigger_state=state,
            confidence=conf,
            structural_resistance_score=1.0 if fail_count >= 2 else 0.7,
            repeated_failure_count=fail_count,
            proposed_objective=f"Investigación forense de causa raíz en el dominio {domain}.",
            proposed_scope=f"Análisis estructural profundo de {domain}, revision de dependencias legacy y auditoría de los {len(relief_ids)} intentos de alivio fallidos.",
            rationale=f"DETECTADA RESISTENCIA ESTRUCTURAL. El dominio no responde a misiones tácticas ({fail_count} fallos confirmados). Se requiere auditoría profunda para evitar degradación sistémica.",
            created_at=datetime.now().isoformat()
        )

    def _persist_audit_proposal(self, conn, p: RootCauseAuditProposal):
        conn.execute("""
            INSERT INTO governance_root_audit_proposals 
            (audit_id, source_heatmap_node, source_relief_ids, trigger_state, confidence, 
             structural_resistance_score, repeated_failure_count, proposed_objective, 
             proposed_scope, rationale, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p.audit_id, p.source_heatmap_node, ",".join(p.source_relief_ids), p.trigger_state, 
            p.confidence, p.structural_resistance_score, p.repeated_failure_count, 
            p.proposed_objective, p.proposed_scope, p.rationale, p.status, p.created_at
        ))
        conn.commit()

audit_trigger_engine = GovernanceAuditTriggerEngine()
