import logging
import uuid
import json
from typing import List, Dict, Any
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from pydantic import BaseModel
from .governance_heatmap_engine import heatmap_engine, HeatmapNode

logger = logging.getLogger(__name__)

class ReliefProposal(BaseModel):
    proposal_id: str
    source_heatmap_node: str
    relief_type: str
    confidence: float
    rationale: str
    proposed_objective: str
    affected_domains: List[str]
    expected_heat_reduction: float
    status: str = "PENDING"
    relief_outcome: Optional[str] = "PENDING"
    baseline_friction_score: Optional[float] = 0.0
    created_at: str

class GovernanceReliefEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE RECOVERY MISSION GENERATOR.
    Transforms structural friction hotspots into governed relief mission proposals.
    """

    def generate_proposals(self) -> List[ReliefProposal]:
        """
        Scans all heatmap nodes and generates relief designs for those above 'HOT' thresholds.
        """
        proposals = []
        nodes = heatmap_engine.get_friction_heatmap()
        
        # Threshold: HOT (>50) or CRITICAL (>80)
        hotspots = [n for n in nodes if n.friction_score >= 50]
        
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    for node in hotspots:
                        # Check for duplicates or already planned relief
                        if self._already_planned(conn, node.domain):
                            continue
                            
                        proposal = self._design_relief(node)
                        if proposal:
                            self._persist_proposal(conn, proposal)
                            proposals.append(proposal)
            except Exception as e:
                logger.error(f"Relief generation failure: {e}")
                        
        return proposals

    def get_active_proposals(self, domain: str = None) -> List[ReliefProposal]:
        """Returns all pending relief proposals, optionally filtered by domain."""
        proposals = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM governance_relief_proposals WHERE status IN ('PENDING', 'ACCEPTED')"
                    params = []
                    if domain:
                        query += " AND source_heatmap_node = ?"
                        params.append(domain)
                    
                    query += " ORDER BY created_at DESC"  # Most recent first
                    rows = conn.execute(query, params).fetchall()
                    for r in rows:
                        proposals.append(ReliefProposal(
                            proposal_id=r["proposal_id"],
                            source_heatmap_node=r["source_heatmap_node"],
                            relief_type=r["relief_type"],
                            confidence=r["confidence"],
                            rationale=r["rationale"],
                            proposed_objective=r["proposed_objective"],
                            affected_domains=json.loads(r["affected_domains"]) if r["affected_domains"] else [],
                            expected_heat_reduction=r["expected_heat_reduction"],
                            status=r["status"],
                            relief_outcome=r["relief_outcome"],
                            baseline_friction_score=r["baseline_friction_score"],
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch relief proposals: {e}")
        return proposals

    def _already_planned(self, conn, domain: str) -> bool:
        """Checks if there's an active proposal or an associated mission already in the roadmap."""
        # 1. Check existing pending proposals
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM governance_relief_proposals WHERE source_heatmap_node = ? AND status = 'PENDING'", 
            (domain,)
        ).fetchone()
        if row["cnt"] > 0: return True
        
        # 2. Check active missions (mocked for this block as handoff registry is complex)
        # We assume if there's an ACCEPTED proposal for this domain, it's already 'under relief'
        row_accepted = conn.execute(
            "SELECT COUNT(*) as cnt FROM governance_relief_proposals WHERE source_heatmap_node = ? AND status = 'ACCEPTED'", 
            (domain,)
        ).fetchone()
        if row_accepted["cnt"] > 0: return True
        
        return False

    def _design_relief(self, node: HeatmapNode) -> ReliefProposal:
        """Heuristic design of a relief mission based on hotspot signals."""
        relief_type = "DOMAIN_RELIEF_MISSION"
        reduction = 20.0
        objective = f"Reducir fricción estructural en el dominio {node.domain}."
        
        if node.severity_band == "CRITICAL":
            relief_type = "HOTSPOT_RECOVERY_PLAN"
            reduction = 40.0
            objective = f"Recuperación crítica: Estabilizar {node.domain} y purgar deuda degradada acumulada."
        elif node.signals.get("advisory_count", 0) > 1:
            relief_type = "ADVISORY_CONSOLIDATION_MISSION"
            reduction = 30.0
            objective = f"Consolidación estructural de advisories en {node.domain}."
        elif node.signals.get("degraded_traces", 0) > 2:
            relief_type = "ROOT_CAUSE_RELIEF_AUDIT"
            reduction = 25.0
            objective = f"Auditoría forense de causa raíz en {node.domain} ante fallos recurrentes."
        
        return ReliefProposal(
            proposal_id=str(uuid.uuid4()),
            source_heatmap_node=node.domain,
            relief_type=relief_type,
            confidence=round(0.7 + (node.friction_score / 400), 2),
            rationale=f"Propuesta generada ante fricción {node.severity_band} ({node.friction_score} pts). {node.rationale}",
            proposed_objective=objective,
            affected_domains=[node.domain],
            expected_heat_reduction=reduction,
            created_at=datetime.now().isoformat()
        )

    def _persist_proposal(self, conn, p: ReliefProposal):
        conn.execute(
            """INSERT INTO governance_relief_proposals 
            (proposal_id, source_heatmap_node, relief_type, confidence, rationale, proposed_objective, affected_domains, expected_heat_reduction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (p.proposal_id, p.source_heatmap_node, p.relief_type, p.confidence, p.rationale, 
             p.proposed_objective, json.dumps(p.affected_domains), p.expected_heat_reduction)
        )
        conn.commit()

    def process_decision(self, proposal_id: str, decision: str) -> Dict[str, Any]:
        """Handles Creator's decision over a relief proposal (ACCEPT, REJECT, POSTPONE)."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT * FROM governance_relief_proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
                if not row: return {"status": "error", "message": "Proposal not found"}
                
                new_status = 'PENDING'
                handoff_id = None
                
                if decision == 'ACCEPT':
                    new_status = 'ACCEPTED'
                    handoff_id = str(uuid.uuid4()) # In real env, we call mission_manager.create_handoff
                    
                    # Capture baseline friction at this exact moment
                    nodes = heatmap_engine.get_friction_heatmap()
                    node = next((n for n in nodes if n.domain == row["source_heatmap_node"]), None)
                    baseline = node.friction_score if node else 0.0
                    
                    conn.execute(
                        "UPDATE governance_relief_proposals SET status = ?, associated_handoff_id = ?, baseline_friction_score = ?, relief_outcome = 'UNDER_OBSERVATION', updated_at = ? WHERE proposal_id = ?",
                        (new_status, handoff_id, baseline, datetime.now().isoformat(), proposal_id)
                    )
                else:
                    if decision == 'REJECT':
                        new_status = 'REJECTED'
                    elif decision == 'POSTPONE':
                        new_status = 'POSTPONED'
                    
                    conn.execute(
                        "UPDATE governance_relief_proposals SET status = ?, updated_at = ? WHERE proposal_id = ?",
                        (new_status, datetime.now().isoformat(), proposal_id)
                    )
                conn.commit()
                
                return {
                    "status": "success", 
                    "decision": decision,
                    "proposal_id": proposal_id,
                    "handoff_id": handoff_id,
                    "target_domain": row["source_heatmap_node"]
                }

relief_engine = GovernanceReliefEngine()
