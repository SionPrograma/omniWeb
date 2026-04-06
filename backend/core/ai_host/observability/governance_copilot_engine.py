import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from .governance_predictive_engine import predictive_engine
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class CopilotSignal(BaseModel):
    signal_type: str  # DRIFT, DEBT_HOTSPOT, ARCHITECTURAL_ANTIPATTERN, RECOIL_WARNING, RECURRENCE_ALARM
    severity: str     # INFO, WARN, CRITICAL
    confidence: float
    rationale: str
    suggested_adjustment: Optional[str] = None
    adjustment_payload: Optional[Dict[str, Any]] = None # Structure: {"type": "ADD_CONSTRAINT", "value": "..."}
    evidence_nodes: List[str] = []

class GovernanceCopilotEngine:
    """
    PHASE 102: MISSION CO-PILOT ENRICHMENT.
    Provides real-time governance assistance during mission design.
    """

    async def analyze_draft(self, objective: str, surface: List[str]) -> List[CopilotSignal]:
        signals = []
        
        # 1. PREDICTIVE DRIFT (From Predictive Engine)
        # We simulate a scan for the affected surfaces
        for s in surface:
            prediction = await predictive_engine.scan_for_drift(s)
            if prediction["prob_score"] > 0.4:
                signals.append(CopilotSignal(
                    signal_type="PREDICTIVE_DRIFT",
                    severity="CRITICAL" if prediction["prob_score"] > 0.7 else "WARN",
                    confidence=prediction["confidence"],
                    rationale=f"Probabilidad de deriva detectada en '{s}': {prediction['rationale']}",
                    suggested_adjustment="Considerar fragmentar la misión o añadir guards de validación específicos para esta capa.",
                    evidence_nodes=prediction["antipattens"]
                ))

        # 2. SEMANTIC DEBT SEARCH (Simulated for this phase)
        # We look for missions in the same surface that failed or caused drift
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                try:
                    # Look for high friction logs in the surface
                    placeholders = ', '.join(['?'] * len(surface))
                    friction_logs = conn.execute(f"SELECT module_name, friction_score, rationale FROM governance_friction_heatmap WHERE module_name IN ({placeholders}) AND friction_score > 50", tuple(surface)).fetchall()
                    
                    for log in friction_logs:
                        signals.append(CopilotSignal(
                            signal_type="DEBT_HOTSPOT",
                            severity="WARN",
                            confidence=0.85,
                            rationale=f"Punto de fricción detectado en '{log['module_name']}': {log['rationale']}",
                            suggested_adjustment=f"Añadir validación estricta de estado en {log['module_name']}.",
                            adjustment_payload={"type": "ADD_CONSTRAINT", "value": f"Validar integridad de estado post-mutación en {log['module_name']}."},
                            evidence_nodes=[log['module_name']]
                        ))
                except Exception as e:
                    logger.error(f"Friction lookup failed: {e}")

        # 3. RECURRENCE ALARM (From Branch Manager)
        # We check if the surface has signals with high recurrence
        from backend.core.ai_host.memory.branch_manager import branch_manager
        for s in surface:
            # Simple heuristic: look for arbitrations mentioning this domain in rationale
            # In a full impl, we'd have a mapping table.
            with db_manager.get_connection() as conn:
                recurrent_refs = conn.execute("SELECT arbitration_id FROM branch_arbitrations WHERE rationale LIKE ? LIMIT 5", (f"%{s}%",)).fetchall()
                for ref in recurrent_refs:
                    risk = branch_manager.analyze_recurrence(ref["arbitration_id"])
                    if risk.recurrence_state in ["RECURRENT", "CRITICAL"]:
                        signals.append(CopilotSignal(
                            signal_type="RECURRENCE_ALARM",
                            severity="CRITICAL",
                            confidence=risk.confidence,
                            rationale=f"Patrón circular detectado en '{s}': {risk.rationale}",
                            suggested_adjustment="Escalar a REVISIÓN ESTRUCTURAL en lugar de parche táctico.",
                            adjustment_payload={"type": "SET_EXECUTION_STYLE", "value": "with_confirmation"},
                            evidence_nodes=[ref["arbitration_id"]]
                        ))

        # 4. STRUCTURAL ANTIPATTERNS (Semantic Analysis placeholder)
        if "reemplazar" in objective.lower() or "borrar" in objective.lower():
            signals.append(CopilotSignal(
                signal_type="ARCHITECTURAL_ANTIPATTERN",
                severity="INFO",
                confidence=0.9,
                rationale="La misión propone reemplazos/borrados masivos. Esto suele generar deuda técnica si no se acompaña de un plan de migración.",
                suggested_adjustment="Añadir regla de compatibilidad heredada (Legacy Shims).",
                adjustment_payload={"type": "ADD_CONSTRAINT", "value": "Asegurar compatibilidad hacia atrás mediante 'Legacy Shims' durante la transición."},
                evidence_nodes=[]
            ))

        return signals

governance_copilot = GovernanceCopilotEngine()
