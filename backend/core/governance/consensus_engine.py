import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class ConsensusAdvisory(BaseModel):
    advisory_id: str
    advisory_type: str
    affected_domains: List[str]
    confidence: float
    recommendation: str
    pattern_summary: str
    ledger_refs: List[str]
    trace_refs: List[str] = []
    severity_band: str = "MODERATE"
    status: str = "PENDING"
    created_at: str

class GovernanceConsensusEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE CONSENSUS ADVISOR ENGINE.
    Analyzes the Decision Ledger to detect behavioral biases and patterns.
    """

    def scan_bias_patterns(self) -> List[ConsensusAdvisory]:
        """
        Scans the ledger and generates recalibration advisories.
        """
        advisories = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Fetch Ledger Entries
                    rows = conn.execute("SELECT * FROM governance_decision_ledger ORDER BY created_at DESC").fetchall()
                    entries = [dict(r) for r in rows]
                    
                    if not entries:
                        return []

                    # 2. RUN PATTERN DETECTORS
                    advisories.extend(self._detect_risk_tolerance_bias(entries))
                    advisories.extend(self._detect_escalation_latency(entries))
                    advisories.extend(self._detect_ineffective_tactic_repetition(entries))
                    advisories.extend(self._detect_excessive_conservatism(entries, conn))

                    # 3. Persist and Filter
                    self._persist_advisories(advisories)
                    
            except Exception as e:
                logger.error(f"Consensus scan failed: {e}")
        
        return advisories

    def _detect_risk_tolerance_bias(self, entries: List[Dict]) -> List[ConsensusAdvisory]:
        """Pattern: RISK_TOLERANCE_TOO_HIGH."""
        bias_list = []
        domain_overrides = {} # domain -> [ledger_ids] (only those that led to DEGRADED)
        
        for e in entries:
            if e['decision_type'] == 'RISK_OVERRIDE' and e['outcome_state'] == 'DEGRADED':
                # Map target_id to domain if it's a branch or search rationale for domain
                domain = e.get('target_id', 'GLOBAL') # Simplified for now
                if domain not in domain_overrides: domain_overrides[domain] = []
                domain_overrides[domain].append(e['ledger_id'])
        
        for domain, refs in domain_overrides.items():
            if len(refs) >= 2:
                bias_list.append(ConsensusAdvisory(
                    advisory_id=f"CA-RISK-{uuid.uuid4().hex[:6].upper()}",
                    advisory_type="RISK_TOLERANCE_TOO_HIGH",
                    affected_domains=[domain],
                    confidence=0.85,
                    pattern_summary=f"Se detecta una tendencia a aceptar riesgos que terminan en degradación operativa en el dominio {domain}.",
                    recommendation=f"Subir el umbral de aceptación de deuda técnica y requerir pre-auditoría obligatoria para el dominio {domain}.",
                    ledger_refs=refs,
                    severity_band="HIGH",
                    created_at=datetime.now().isoformat()
                ))
        return bias_list

    def _detect_escalation_latency(self, entries: List[Dict]) -> List[ConsensusAdvisory]:
        """Pattern: ESCALATION_TOO_LATE."""
        bias_list = []
        # Find escalations that happened AFTER multiple failed attempts
        # Simplified: Many entries for same target_id where latest is ESCALATED and previous were FAIL/DEGRADED
        target_history = {}
        for e in entries:
            tid = e['target_id']
            if tid not in target_history: target_history[tid] = []
            target_history[tid].append(e)
            
        for tid, history in target_history.items():
            late_escalation = False
            refs = [h['ledger_id'] for h in history]
            # If latest (history[0]) is ESCALATED/SUPERSEDED and we had degradation before
            if any(h['outcome_state'] == 'DEGRADED' for h in history) and any(h['action_taken'] in ['ESCALATE', 'ESCALATED'] for h in history):
                late_escalation = True
                
            if late_escalation and len(history) >= 2:
                bias_list.append(ConsensusAdvisory(
                    advisory_id=f"CA-LAT-{uuid.uuid4().hex[:6].upper()}",
                    advisory_type="ESCALATION_TOO_LATE",
                    affected_domains=["GLOBAL"],
                    confidence=0.7,
                    pattern_summary=f"Patrón de escalado reactivo detectado para el objeto {tid}. El sistema escala después de intentos fallidos de gestión local.",
                    recommendation="Reducir el tiempo de permanencia en estado de deuda aceptada y escalar automáticamente tras la segunda señal de deriva.",
                    ledger_refs=refs,
                    severity_band="MODERATE",
                    created_at=datetime.now().isoformat()
                ))
        return bias_list

    def _detect_ineffective_tactic_repetition(self, entries: List[Dict]) -> List[ConsensusAdvisory]:
        """Pattern: REPEAT_INEFFECTIVE_TACTIC."""
        bias_list = []
        tactic_counts = {} # action_taken -> [ledger_ids]
        
        for e in entries:
            if e['outcome_state'] == 'DEGRADED':
                action = e['action_taken']
                if action not in tactic_counts: tactic_counts[action] = []
                tactic_counts[action].append(e['ledger_id'])
                
        for action, refs in tactic_counts.items():
            if len(refs) >= 3:
                bias_list.append(ConsensusAdvisory(
                    advisory_id=f"CA-TACT-{uuid.uuid4().hex[:6].upper()}",
                    advisory_type="REPEAT_INEFFECTIVE_TACTIC",
                    affected_domains=["GLOBAL"],
                    confidence=0.9,
                    pattern_summary=f"La táctica '{action}' ha resultado ineficaz en {len(refs)} ocasiones recientes, resultando en degradación.",
                    recommendation=f"Evitar el uso de '{action}' como medida paliativa y priorizar acciones correctivas de raíz (Root Cause Audit).",
                    ledger_refs=refs,
                    severity_band="CRITICAL",
                    created_at=datetime.now().isoformat()
                ))
        return bias_list

    def _detect_excessive_conservatism(self, entries: List[Dict], conn) -> List[ConsensusAdvisory]:
        """Pattern: OVER_CONSERVATIVE_PATTERN."""
        bias_list = []
        ignored_paths = [e for e in entries if e['decision_type'] == 'ALTERNATIVE_PATH_ACTION' and e['action_taken'] in ['IGNORED', 'REJECTED']]
        
        if len(ignored_paths) >= 3:
            refs = [p['ledger_id'] for p in ignored_paths]
            bias_list.append(ConsensusAdvisory(
                advisory_id=f"CA-CONS-{uuid.uuid4().hex[:6].upper()}",
                advisory_type="OVER_CONSERVATIVE_PATTERN",
                affected_domains=["STRATEGIC"],
                confidence=0.65,
                pattern_summary="Se detecta un patrón de rechazo sistemático de alternativas de alto retorno táctico/ROI.",
                recommendation="Revisar el 'Risk Appetite' del sistema. Se están perdiendo oportunidades de saneamiento estructural por cautela excesiva.",
                ledger_refs=refs,
                severity_band="LOW",
                created_at=datetime.now().isoformat()
            ))
        return bias_list

    def _persist_advisories(self, advisories: List[ConsensusAdvisory]):
        """Saves generated advisories to DB, avoiding duplicates of active patterns."""
        with db_manager.get_connection() as conn:
            for a in advisories:
                # Check for existing PENDING advisory of same type
                exists = conn.execute("SELECT 1 FROM governance_consensus_advisories WHERE advisory_type = ? AND status = 'PENDING'", (a.advisory_type,)).fetchone()
                if not exists:
                    conn.execute("""
                        INSERT INTO governance_consensus_advisories (
                            advisory_id, advisory_type, affected_domains, confidence,
                            recommendation, pattern_summary, ledger_refs, trace_refs,
                            severity_band, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        a.advisory_id, a.advisory_type, json.dumps(a.affected_domains), a.confidence,
                        a.recommendation, a.pattern_summary, json.dumps(a.ledger_refs), json.dumps(a.trace_refs),
                        a.severity_band, a.created_at
                    ))
            conn.commit()

    def get_active_advisories(self) -> List[ConsensusAdvisory]:
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM governance_consensus_advisories WHERE status = 'PENDING' ORDER BY created_at DESC").fetchall()
                    for r in rows:
                        results.append(ConsensusAdvisory(
                            advisory_id=r["advisory_id"],
                            advisory_type=r["advisory_type"],
                            affected_domains=json.loads(r["affected_domains"]),
                            confidence=r["confidence"],
                            recommendation=r["recommendation"],
                            pattern_summary=r["pattern_summary"],
                            ledger_refs=json.loads(r["ledger_refs"]),
                            trace_refs=json.loads(r["trace_refs"]),
                            severity_band=r["severity_band"],
                            status=r["status"],
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch consensus: {e}")
        return results

    def act_on_advisory(self, advisory_id: str, action: str):
        """Updates advisory status: ATTEND, IGNORE."""
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    conn.execute("UPDATE governance_consensus_advisories SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE advisory_id = ?", (action, advisory_id))
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to update consensus advisory: {e}")

consensus_engine = GovernanceConsensusEngine()
