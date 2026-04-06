import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .governance_predictive_engine import predictive_engine
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class ChatSignal(BaseModel):
    signal_id: str
    signal_type: str  # DOMAIN_DEBT, PREDICTIVE_DRIFT, ANTIPATTERN, MISSION_SPLIT_SUGGESTION
    severity_band: str # INFO, WARN, CRITICAL
    target_domain: Optional[str]
    confidence: float
    rationale: str
    suggested_adjustment: Optional[str] = None
    adjustment_payload: Optional[Dict[str, Any]] = None
    dismissible: bool = True

class ConversationalGovernanceEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE CHAT ENRICHMENT LAYER.
    Analyzes ongoing designs in chat to inject evidence-based preventive signals.
    """

    async def analyze_interaction(self, message: str, context: Dict[str, Any]) -> List[ChatSignal]:
        signals = []
        user_id = context.get("user_id")

        # 1. Identify Domains and Intent
        domains = self._extract_domains(message)
        intent = self._detect_intent(message)

        # 2. Skip if no operational intent detected (Low Noise Rule)
        if not intent:
            return []

        # 3. For each domain, correlate with governance data
        for domain in domains:
            # Check Cooldown (Anti-Spam Rule)
            if self._is_under_cooldown(domain, user_id):
                continue

            # A. PREDICTIVE DRIFT
            prediction = await predictive_engine.scan_for_drift(domain)
            if prediction["prob_score"] > 0.45:
                signals.append(ChatSignal(
                    signal_id=f"gsig-{uuid.uuid4().hex[:6]}",
                    signal_type="PREDICTIVE_DRIFT",
                    severity_band="CRITICAL" if prediction["prob_score"] > 0.7 else "WARN",
                    target_domain=domain,
                    confidence=prediction["confidence"],
                    rationale=f"Deriva predictiva detectada en '{domain}': {prediction['rationale']}",
                    suggested_adjustment="Dividir la misión o añadir guards estructurales.",
                    adjustment_payload={"type": "SET_EXECUTION_STYLE", "value": "with_confirmation"}
                ))

            # B. DOMAIN DEBT (Hotspots)
            friction = self._get_domain_friction(domain)
            if friction > 0.6:
                signals.append(ChatSignal(
                    signal_id=f"gsig-{uuid.uuid4().hex[:6]}",
                    signal_type="DOMAIN_DEBT",
                    severity_band="WARN",
                    target_domain=domain,
                    confidence=0.85,
                    rationale=f"'{domain}' se encuentra bajo presión técnica elevada.",
                    suggested_adjustment=f"Reducir el alcance o priorizar saneamiento en {domain}."
                ))

            # C. RECURRENCE RISK
            recurrence = self._get_recurrence_risk(domain)
            if recurrence and recurrence["state"] in ["RECURRENT", "CRITICAL"]:
                signals.append(ChatSignal(
                    signal_id=f"gsig-{uuid.uuid4().hex[:6]}",
                    signal_type="RECURRENCE_ALARM",
                    severity_band="CRITICAL",
                    confidence=0.9,
                    target_domain=domain,
                    rationale=f"Patrón de recaída circular en {domain}: {recurrence['rationale']}",
                    suggested_adjustment="Lanzar Auditoría de Causa Raíz antes de proponer cambios.",
                    adjustment_payload={"type": "OPEN_ADVISORY", "domain": domain}
                ))

        # 4. Persistence and Cleanup (Only if signals generated)
        if signals:
            self._persist_signals(signals, context.get("conversation_id"))

        return signals

    def _extract_domains(self, text: str) -> List[str]:
        # Placeholder for NER or regex-based domain extraction.
        # In OmniWeb, we look for module names, core components, or service IDs.
        matches = []
        known_modules = ["auth", "router", "database", "ui", "api", "governance", "handoff", "editor"]
        for m in known_modules:
            if m in text.lower():
                matches.append(m)
        return list(set(matches))

    def _detect_intent(self, text: str) -> bool:
        # Detect if the user is proposing a change or mission.
        action_keywords = ["cambiar", "reemplazar", "borrar", "implementar", "añadir", "crear", "mission", "misión", "fix"]
        return any(k in text.lower() for k in action_keywords)

    def _is_under_cooldown(self, domain: str, user_id: str) -> bool:
        # 10 minutes cooldown for the same signal type/domain
        cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                res = conn.execute("""
                    SELECT COUNT(*) as cnt FROM governance_chat_signals 
                    WHERE target_domain = ? AND created_at > ?
                """, (domain, cutoff)).fetchone()
                return res["cnt"] > 0

    def _get_domain_friction(self, domain: str) -> float:
        # Mock/Integration with HeatmapEngine
        from .governance_heatmap_engine import heatmap_engine
        heatmap = heatmap_engine.get_friction_heatmap(skip_evaluation=True)
        node = next((n for n in heatmap if domain in n.domain.lower()), None)
        return node.friction_score / 100.0 if node else 0.0

    def _get_recurrence_risk(self, domain: str) -> Optional[Dict[str, Any]]:
        # Mock/Integration with BranchManager
        from backend.core.ai_host.memory.branch_manager import branch_manager
        with db_manager.get_connection() as conn:
            # Look for recent arbitrations in this domain
            arb = conn.execute("SELECT arbitration_id FROM branch_arbitrations WHERE rationale LIKE ? LIMIT 1", (f"%{domain}%",)).fetchone()
            if arb:
                risk = branch_manager.analyze_recurrence(arb["arbitration_id"])
                return {"state": risk.recurrence_state, "rationale": risk.rationale}
        return None

    def _persist_signals(self, signals: List[ChatSignal], conv_id: Optional[str]):
        now = datetime.utcnow().isoformat()
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                for s in signals:
                    conn.execute("""
                        INSERT INTO governance_chat_signals (
                            signal_id, conversation_id, signal_type, target_domain,
                            severity_band, confidence, rationale, suggested_adjustment, 
                            adjustment_payload, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        s.signal_id, conv_id, s.signal_type, s.target_domain,
                        s.severity_band, s.confidence, s.rationale, 
                        s.suggested_adjustment, json.dumps(s.adjustment_payload) if s.adjustment_payload else None,
                        now
                    ))
                conn.commit()

chat_governance_engine = ConversationalGovernanceEngine()
