import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class CreatorAuditService:
    """
    OMNI_CREATOR_AUDIT_SURFACE — BLOCK 05: EVIDENCE AGGREGATION.
    Consolidates mission outcomes, artifacts, and governance signals.
    """
    
    def get_audit_summary(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Aggregates recent mission outcomes with their linked evidence.
        Uses a read-only consolidation across multiple governance tables.
        """
        audit_feed = []
        
        # We set context to 'core' to ensures proper permission propagation 
        with set_chip_context("core"):
            try:
                # We use internal=True for read-only aggregation as it's safe for Creator access
                with db_manager.get_connection(internal=True) as conn:
                    # 1. Fetch recent missions
                    # We capture the tactical objective and status first.
                    missions = conn.execute("""
                        SELECT mission_id, active_goal, status, context_snap, created_at, updated_at, friction, preconditions_ok
                        FROM system_missions 
                        ORDER BY updated_at DESC LIMIT ?
                    """, (limit,)).fetchall()
                    
                    for m in missions:
                        m_id = m["mission_id"]
                        
                        # 2. Rehydrate artifacts from the mission snap
                        # MissionManager stores artifacts in context_snap["artifacts"] as a JSON list.
                        artifacts = []
                        try:
                            snap = json.loads(m["context_snap"] or "{}")
                            artifacts = snap.get("artifacts", [])
                        except: pass
                        
                        # 3. Join Governance Decisions (Strategic Ledger)
                        # Find any strategic pivots or risk overrides linked to this mission ID.
                        ledger = conn.execute("""
                            SELECT ledger_id, decision_type, action_taken, rationale, evidence_refs, severity_context
                            FROM governance_decision_ledger 
                            WHERE target_id = ? 
                            OR (target_ref_type = 'MISSION' AND target_id = ?)
                            ORDER BY created_at DESC
                        """, (m_id, m_id)).fetchall()
                        
                        gov_decisions = []
                        for l in ledger:
                            try:
                                ev_refs = json.loads(l["evidence_refs"] or "{}")
                            except: ev_refs = {}
                            
                            gov_decisions.append({
                                "id": l["ledger_id"],
                                "type": l["decision_type"],
                                "action": l["action_taken"],
                                "rationale": l["rationale"],
                                "evidence_refs": ev_refs,
                                "severity": l["severity_context"]
                            })
                        
                        # 4. Fetch Outcome Verification (Post-Mission Sync / Autopsy)
                        # This bridges the 'intended' value with the 'actual' outcome friction.
                        verification = None
                        try:
                            # Note: governance_post_mission_syncs is the table from the Wisdom Sync engine
                            sync = conn.execute("""
                                SELECT sync_id, actual_outcome_type, rationale, execution_context_quality, supporting_evidence
                                FROM governance_post_mission_syncs 
                                WHERE source_mission_id = ?
                                LIMIT 1
                            """, (m_id,)).fetchone()
                            
                            if sync:
                                verification = {
                                    "sync_id": sync["sync_id"],
                                    "outcome_type": sync["actual_outcome_type"],
                                    "rationale": sync["rationale"],
                                    "quality": sync["execution_context_quality"]
                                }
                        except: 
                            # If table doesn't exist yet in the DB instance, we skip silently
                            pass
                        
                        # 5. Build Unified Model
                        audit_feed.append({
                            "mission_id": m_id,
                            "goal": m["active_goal"],
                            "status": m["status"],
                            "timestamp": m["updated_at"],
                            "artifacts": artifacts,
                            "governance": {
                                "decisions": gov_decisions,
                                "verification": verification
                            },
                            "trust_metrics": {
                                "friction": m["friction"],
                                "preconditions_ok": bool(m["preconditions_ok"]),
                                "evidence_status": "VERIFIED" if verification else "PENDING_VERIFICATION" if artifacts else "MISSING"
                            }
                        })
                        
            except Exception as e:
                logger.error(f"[CREATOR_AUDIT] Failed to aggregate evidence: {e}")
                
        return audit_feed

    def get_structural_debt(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        OMNI_CREATOR_AUDIT_SURFACE — BLOCK 07: STRUCTURAL DEBT MONITOR.
        Analyzes historical mission patterns to detect recurring weak points/debt.
        """
        debt_clusters = {}
        
        with set_chip_context("core"):
            try:
                # We use internal=True for read-only aggregation as it's safe for Creator access
                with db_manager.get_connection(internal=True) as conn:
                    # Fetch all missions within recent history for pattern matching
                    missions = conn.execute("""
                        SELECT m.mission_id, m.active_goal, m.context_snap, m.updated_at, m.friction, 
                               s.actual_outcome_type as outcome, s.rationale
                        FROM system_missions m
                        LEFT JOIN governance_post_mission_syncs s ON m.mission_id = s.source_mission_id
                        ORDER BY m.updated_at DESC LIMIT 50
                    """).fetchall()

                    for m in missions:
                        # 1. Infer Sector from Artifact Paths or Goal
                        artifacts = []
                        try:
                            snap = json.loads(m["context_snap"] or "{}")
                            artifacts = snap.get("artifacts", [])
                        except: pass
                        
                        sector = "GENERAL"
                        if artifacts:
                            # Use first representative artifact to guess folder
                            first = artifacts[0].replace("\\", "/")
                            parts = first.split("/")
                            if len(parts) >= 2:
                                sector = "/".join(parts[:2]) # e.g. backend/core
                            else:
                                sector = parts[0]
                        elif ":" in m["active_goal"]:
                            sector = m["active_goal"].split(":")[0].strip()

                        # 2. Cluster logic
                        if sector not in debt_clusters:
                            debt_clusters[sector] = {
                                "sector": sector,
                                "missions": [],
                                "conflict_count": 0,
                                "total_friction": 0,
                                "latest_timestamp": m["updated_at"],
                                "severity": "WEAK",
                                "evidence_count": 0
                            }
                        
                        cluster = debt_clusters[sector]
                        cluster["missions"].append(m["mission_id"])
                        cluster["total_friction"] += (m["friction"] or 0)
                        cluster["evidence_count"] += 1
                        
                        if m["outcome"] in ["CONFLICT", "DOWNSIDE"]:
                            cluster["conflict_count"] += 1

                    # 3. Refine Severity & Verification Confidence
                    results = []
                    for s, c in debt_clusters.items():
                        # Structural Debt Rule: 2+ conflicts or high friction is Moderate/Critical
                        avg_friction = c["total_friction"] / len(c["missions"]) if c["missions"] else 0
                        
                        if c["conflict_count"] >= 2 or (c["conflict_count"] >= 1 and avg_friction > 0.6):
                            c["severity"] = "CRITICAL"
                        elif c["conflict_count"] >= 1 or avg_friction > 0.4:
                            c["severity"] = "MODERATE"
                        
                        # Only return sectors with identifiable 'debt' or enough evidence
                        if len(c["missions"]) >= 2 or c["conflict_count"] > 0:
                            results.append(c)

                    # Sort by severity priority
                    sev_map = {"CRITICAL": 3, "MODERATE": 2, "WEAK": 1}
                    results.sort(key=lambda x: (sev_map[x["severity"]], x["conflict_count"]), reverse=True)
                    return results[:limit]

            except Exception as e:
                logger.error(f"[CREATOR_AUDIT] Debt analysis failed: {e}")
                return []

creator_audit_service = CreatorAuditService()
