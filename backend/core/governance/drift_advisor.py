import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class DriftAdvisor:
    """
    OMNIWEB — BLOQUE: OMNI_CATALYST_V0.7.
    Strategic Drift Alerting Service.
    Consolidates high-signal governance events into compact Pulse Alerts.
    """
    
    def __init__(self):
        # Default thresholds (will load from DB if available)
        self.pulse_threshold = 3
        self.window_days = 7

    def _load_params(self):
        try:
            with db_manager.get_connection() as conn:
                res = conn.execute("SELECT param_key, current_value FROM governance_engine_parameters WHERE engine_name = 'DRIFT_ADVISOR'").fetchall()
                for row in res:
                    if row["param_key"] == "PULSE_THRESHOLD":
                        self.pulse_threshold = int(row["current_value"])
                    elif row["param_key"] == "PULSE_WINDOW_DAYS":
                        self.window_days = int(row["current_value"])
        except Exception as e:
            logger.error(f"Drift Advisor: Failed to load parameters: {e}")

    def refresh_pulse_alerts(self, project_id: str = "PROJECT_OMNIWEB_PROD") -> List[Dict[str, Any]]:
        """
        Main entry point for calculating current strategic drift.
        Synchronizes the pulse_alerts table with fresh signal aggregations.
        """
        self._load_params()
        new_alerts = []
        
        with set_chip_context("core"):
            # 1. Aggregate Policy Rejects (From Decision Ledger)
            policy_pulses = self._aggregate_policy_rejects(project_id)
            new_alerts.extend(policy_pulses)
            
            # 2. Aggregate Wisdom Contradictions (From Feedback/Replay Ledger)
            wisdom_pulses = self._aggregate_wisdom_contradictions(project_id)
            new_alerts.extend(wisdom_pulses)
            
            # 3. Persist and return
            self._persist_pulse_alerts(new_alerts, project_id)
            
        return new_alerts

    def _aggregate_policy_rejects(self, project_id: str) -> List[Dict[str, Any]]:
        """Consolidates repeated catalyst rejections into pulse alerts."""
        limit_date = (datetime.utcnow() - timedelta(days=self.window_days)).isoformat()
        
        with db_manager.get_connection() as conn:
            # We look for recurring patterns in evidence_refs
            rejections = conn.execute("""
                SELECT ledger_id, evidence_refs, created_at
                FROM governance_decision_ledger
                WHERE decision_type IN ('CATALYST_POLICY_REJECT', 'CATALYST_CONTRACT_REJECT')
                  AND created_at > ?
                  AND project_id = ?
            """, (limit_date, project_id)).fetchall()
            
        clusters = {}
        for r in rejections:
            try:
                refs = json.loads(r["evidence_refs"])
                pattern = refs.get("pattern", "unknown_fault")
                if pattern not in clusters:
                    clusters[pattern] = {"ids": [], "domains": set(), "last_seen": r["created_at"]}
                clusters[pattern]["ids"].append(r["ledger_id"])
                # Extract domain from evidence_refs if available
                domain = refs.get("domain_id") or refs.get("domain")
                if domain:
                    clusters[pattern]["domains"].add(domain)
                if r["created_at"] > clusters[pattern]["last_seen"]:
                    clusters[pattern]["last_seen"] = r["created_at"]
            except: continue
            
        import hashlib
        def make_stable_id(prefix, sub):
            raw = f"{prefix}:{sub}:{project_id}"
            return f"PULSE-{prefix[:4]}-{hashlib.md5(raw.encode()).hexdigest()[:8].upper()}"

        alerts = []
        for pattern, data in clusters.items():
            count = len(data["ids"])
            if count >= self.pulse_threshold:
                # Decide confidence
                confidence = "OBSERVATION"
                if count >= 10: confidence = "CRITICAL"
                elif count >= 5: confidence = "ELEVATED"
                
                alerts.append({
                    "alert_id": make_stable_id("PLCY", pattern),
                    "alert_type": "POLICY_DRIFT_ALERT",
                    "subject_ref": pattern,
                    "occurrence_count": count,
                    "confidence": confidence,
                    "rationale": f"Recurring rejection pattern '{pattern}' detected {count} times. Suggest policy hardening update.",
                    "evidence_ids": json.dumps(data["ids"]),
                    "domain_context": list(data["domains"])[0] if data["domains"] else None,
                    "last_seen_at": data["last_seen"]
                })
        return alerts

    def _aggregate_wisdom_contradictions(self, project_id: str) -> List[Dict[str, Any]]:
        """Consolidates repeated wisdom contradictions."""
        import hashlib
        def make_stable_id(prefix, sub):
            raw = f"{prefix}:{sub}:{project_id}"
            return f"PULSE-{prefix[:4]}-{hashlib.md5(raw.encode()).hexdigest()[:8].upper()}"

        limit_date = (datetime.utcnow() - timedelta(days=self.window_days)).isoformat()
        
        with db_manager.get_connection() as conn:
            # Check governance_wisdom_feedback (Phase 113)
            # or governance_strategic_replay_ledger
            # We'll use wisdom_feedback as it's more direct
            contradictions = conn.execute("""
                SELECT feedback_id, source_atlas_node_ref, created_at
                FROM governance_wisdom_feedback
                WHERE feedback_state = 'CONTRADICTED'
                  AND created_at > ?
            """, (limit_date,)).fetchall()
            
        clusters = {}
        for c in contradictions:
            node = c["source_atlas_node_ref"]
            if node not in clusters:
                clusters[node] = {"ids": [], "last_seen": c["created_at"]}
            clusters[node]["ids"].append(c["feedback_id"])
            if c["created_at"] > clusters[node]["last_seen"]:
                clusters[node]["last_seen"] = c["created_at"]
                
        alerts = []
        for node, data in clusters.items():
            count = len(data["ids"])
            if count >= self.pulse_threshold:
                alerts.append({
                    "alert_id": make_stable_id("WSDM", node),
                    "alert_type": "WISDOM_CONTRADICTOR_ALERT",
                    "subject_ref": f"node:{node}",
                    "occurrence_count": count,
                    "confidence": "CRITICAL" if count >= 3 else "ELEVATED",
                    "rationale": f"Tactical Wisdom Node '{node}' has been contradicted by outcomes {count} times. Prediction model is officially drifting.",
                    "evidence_ids": json.dumps(data["ids"]),
                    "domain_context": "Strategic Alignment",
                    "last_seen_at": data["last_seen"]
                })
        return alerts

    def _persist_pulse_alerts(self, alerts: List[Dict[str, Any]], project_id: str):
        """Saves or updates pulse alerts in the persistent table."""
        with db_manager.get_connection() as conn:
            for a in alerts:
                conn.execute("""
                    INSERT INTO governance_pulse_alerts (
                        alert_id, alert_type, subject_ref, occurrence_count, confidence, 
                        rationale, evidence_ids, domain_context, last_seen_at, project_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(alert_id) DO UPDATE SET
                        occurrence_count=excluded.occurrence_count,
                        confidence=excluded.confidence,
                        last_seen_at=excluded.last_seen_at,
                        rationale=excluded.rationale,
                        evidence_ids=excluded.evidence_ids
                    WHERE status = 'PENDING_REVIEW'
                """, (
                    a["alert_id"], a["alert_type"], a["subject_ref"], a["occurrence_count"],
                    a["confidence"], a["rationale"], a["evidence_ids"], a["domain_context"],
                    a["last_seen_at"], project_id
                ))
            conn.commit()

    def get_active_pulses(self) -> List[Dict[str, Any]]:
        """Returns PENDING_REVIEW alerts from the store."""
        with db_manager.get_connection() as conn:
            res = conn.execute("SELECT * FROM governance_pulse_alerts WHERE status = 'PENDING_REVIEW' ORDER BY confidence DESC, last_seen_at DESC").fetchall()
            return [dict(r) for r in res]

    def resolve_pulse(self, alert_id: str, decision: str):
        """Marks an alert as reviewed."""
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE governance_pulse_alerts SET status = ? WHERE alert_id = ?", (decision, alert_id))
            conn.commit()

drift_advisor = DriftAdvisor()
