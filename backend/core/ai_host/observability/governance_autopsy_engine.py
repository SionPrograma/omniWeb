import logging
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class BranchAutopsy(BaseModel):
    autopsy_id: str
    branch_id: str
    branch_goal_summary: str
    affected_domains: List[str]
    hotspot_history: List[Dict[str, Any]]
    advisories_generated: List[Dict[str, Any]]
    creator_actions_summary: List[str]
    debt_events: List[Dict[str, Any]]
    resistance_events: List[Dict[str, Any]]
    root_audit_events: List[Dict[str, Any]]
    final_branch_outcome: str
    lessons_learned: List[str]
    structural_findings: List[str]
    recommended_followup: List[str]
    confidence: float
    created_at: str

class GovernanceBranchAutopsyEngine:
    """
    OMNIWEB — BLOQUE: FORENSIC BRANCH AUTOPSY ENGINE.
    Analyzes branch history post-experiment to distill structural learning.
    """

    def generate_autopsy(self, branch_id: str, outcome: str) -> Optional[BranchAutopsy]:
        """
        Reconstructs the story of a branch and generates a permanent forensic autopsy.
        """
        logger.info(f"Generating autopsy for branch {branch_id} with outcome {outcome}")
        
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Basic Branch Data
                    branch_row = conn.execute("SELECT * FROM roadmap_branches WHERE branch_id = ?", (branch_id,)).fetchone()
                    if not branch_row:
                        logger.error(f"Branch {branch_id} not found for autopsy.")
                        return None
                    
                    # 2. Reconstruct Missions & Interventions
                    missions = conn.execute("SELECT * FROM mission_handoffs WHERE branch_id = ?", (branch_id,)).fetchall()
                    handoff_ids = [m["handoff_id"] for m in missions]
                    
                    relief_history = []
                    if handoff_ids:
                        placeholders = ",".join(["?"] * len(handoff_ids))
                        relief_history = conn.execute(
                            f"SELECT * FROM governance_relief_proposals WHERE associated_handoff_id IN ({placeholders})",
                            handoff_ids
                        ).fetchall()

                    # 3. Structural Resistance & Root Audits
                    root_audits = []
                    if handoff_ids:
                        root_audits = conn.execute(
                            f"SELECT * FROM governance_root_audit_proposals WHERE associated_handoff_id IN ({placeholders})",
                            handoff_ids
                        ).fetchall()

                    # 4. Synthesize Findings
                    affected_domains = list(set([json.loads(m["surface_affected"])[0] if m["surface_affected"] else "Unknown" for m in missions]))
                    hotspot_history = [{"domain": r["source_heatmap_node"], "outcome": r["relief_outcome"]} for r in relief_history]
                    
                    creator_actions = []
                    if outcome == "MERGED": creator_actions.append("Branch changes fully integrated into main roadmap.")
                    elif outcome == "DISCARDED": creator_actions.append("Branch abandoned due to structural tension or goal shift.")

                    lessons = []
                    findings = []
                    followup = []
                    
                    # Intelligence Layer: Evaluate Relief Effectiveness
                    effective_count = len([r for r in relief_history if r["relief_outcome"] == "EFFECTIVE_RELIEF"])
                    failed_count = len([r for r in relief_history if r["relief_outcome"] in ["RESISTANT_HOTSPOT", "RELIEF_INEFFECTIVE"]])
                    
                    if effective_count > 0:
                        lessons.append(f"Tactical relief was successful in {effective_count} domains.")
                    if failed_count > 0:
                        findings.append(f"Structural resistance detected in {failed_count} relief attempts, indicating deep-rooted debt.")
                        lessons.append("Tactical patches are insufficient for core resistance; structural refactor recommended.")
                        followup.append("Initiate follow-up structural advisory for resistant domains.")

                    if len(root_audits) > 0:
                        findings.append(f"Branch triggered {len(root_audits)} deep forensic root cause audits.")
                        followup.append("Review completed audit results before further iterations in related domains.")

                    autopsy = BranchAutopsy(
                        autopsy_id=str(uuid.uuid4()),
                        branch_id=branch_id,
                        branch_goal_summary=f"Analysis of experiment: {branch_row['name']}",
                        affected_domains=affected_domains,
                        hotspot_history=hotspot_history,
                        advisories_generated=[], # To be linked if available
                        creator_actions_summary=creator_actions,
                        debt_events=[],
                        resistance_events=[h for h in hotspot_history if h["outcome"] == "RESISTANT_HOTSPOT"],
                        root_audit_events=[{"id": a["audit_id"], "domain": a["source_heatmap_node"]} for a in root_audits],
                        final_branch_outcome=outcome,
                        lessons_learned=lessons or ["Nominal branch execution without critical deviations."],
                        structural_findings=findings or ["No significant structural resistance detected during experiment."],
                        recommended_followup=followup or ["Continuous monitoring of affected domains."],
                        confidence=0.9 if relief_history else 0.7,
                        created_at=datetime.now().isoformat()
                    )

                    # 5. Persist Autopsy
                    self._persist_autopsy(conn, autopsy)
                    return autopsy

            except Exception as e:
                logger.error(f"Autopsy generation failed for {branch_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None

    def _persist_autopsy(self, conn, a: BranchAutopsy):
        conn.execute("""
            INSERT INTO governance_branch_autopsies (
                autopsy_id, branch_id, branch_goal_summary, affected_domains, 
                hotspot_history, advisories_generated, creator_actions_summary, 
                debt_events, resistance_events, root_audit_events, 
                final_branch_outcome, lessons_learned, structural_findings, 
                recommended_followup, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a.autopsy_id, a.branch_id, a.branch_goal_summary, json.dumps(a.affected_domains),
            json.dumps(a.hotspot_history), json.dumps(a.advisories_generated),
            json.dumps(a.creator_actions_summary), json.dumps(a.debt_events),
            json.dumps(a.resistance_events), json.dumps(a.root_audit_events),
            a.final_branch_outcome, json.dumps(a.lessons_learned),
            json.dumps(a.structural_findings), json.dumps(a.recommended_followup),
            a.confidence, a.created_at
        ))
        conn.commit()

    def get_autopsies(self, branch_id: Optional[str] = None) -> List[BranchAutopsy]:
        """Retrieves autopsy reports."""
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM governance_branch_autopsies"
                    params = []
                    if branch_id:
                        query += " WHERE branch_id = ?"
                        params.append(branch_id)
                    
                    rows = conn.execute(query, params).fetchall()
                    for r in rows:
                        results.append(BranchAutopsy(
                            autopsy_id=r["autopsy_id"],
                            branch_id=r["branch_id"],
                            branch_goal_summary=r["branch_goal_summary"],
                            affected_domains=json.loads(r["affected_domains"]),
                            hotspot_history=json.loads(r["hotspot_history"]),
                            advisories_generated=json.loads(r["advisories_generated"]),
                            creator_actions_summary=json.loads(r["creator_actions_summary"]),
                            debt_events=json.loads(r["debt_events"]),
                            resistance_events=json.loads(r["resistance_events"]),
                            root_audit_events=json.loads(r["root_audit_events"]),
                            final_branch_outcome=r["final_branch_outcome"],
                            lessons_learned=json.loads(r["lessons_learned"]),
                            structural_findings=json.loads(r["structural_findings"]),
                            recommended_followup=json.loads(r["recommended_followup"]),
                            confidence=r["confidence"],
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch autopsies: {e}")
        return results

autopsy_engine = GovernanceBranchAutopsyEngine()
