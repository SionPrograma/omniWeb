import logging
import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.handoff_manager import handoff_manager

logger = logging.getLogger(__name__)

class CreatorPersona(BaseModel):
    persona_id: str
    name: str
    role: str # ARCHITECT, DESIGNER, TESTER, OPERATOR, AUDITOR, CREATOR_CORE
    weight: float = 1.0 # Priority weight in conflicts
    scope: List[str] = [] # preferred surfaces/domains

class VisionConflict(BaseModel):
    conflict_id: str
    type: str # PRIORITY_CONFLICT, DOMAIN_COLLISION, METHOD_CONFLICT, REDUNDANCY
    involved_handoffs: List[str]
    personas: List[str]
    description: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    suggested_arbitration: str
    resolution_status: str = "PENDING" # PENDING, RESOLVED, ESCALATED

class PersonaSyncManager:
    """
    OMNIWEB — BLOQUE: MULTI-PERSONA CREATOR SYNC.
    Coordinates multiple creator perspectives/roles within the roadmap.
    """
    
    def __init__(self):
        self.personas = {
            "ARCHITECT": CreatorPersona(persona_id="p_arch", name="Architect", role="ARCHITECT", weight=1.2, scope=["core", "backend", "db"]),
            "DESIGNER": CreatorPersona(persona_id="p_dsgn", name="Designer", role="DESIGNER", weight=1.0, scope=["ui", "general"]),
            "TESTER": CreatorPersona(persona_id="p_test", name="Tester", role="TESTER", weight=1.0, scope=["tests", "validation"]),
            "AUDITOR": CreatorPersona(persona_id="p_audt", name="Auditor", role="AUDITOR", weight=1.1, scope=["security", "governance"]),
            "CREATOR_CORE": CreatorPersona(persona_id="p_core", name="Creator Core", role="CREATOR_CORE", weight=100.0)
        }

    def detect_vision_conflicts(self) -> List[VisionConflict]:
        conflicts = []
        handoffs = handoff_manager.get_all()
        
        # 1. Surface Overlap between personas
        surface_map = {} # surface -> [handoffs]
        for h in handoffs:
            if h.readiness_state in ["ARCHIVED", "ABORTED"]: continue
            for surface in h.surface_affected:
                if surface not in surface_map: surface_map[surface] = []
                surface_map[surface].append(h)

        for surface, missions in surface_map.items():
            if len(missions) > 1:
                p_involved = list(set([getattr(m, "origin_persona", "CREATOR_CORE") for m in missions]))
                if len(p_involved) > 1:
                    cid = hashlib.md5(f"collision:{surface}".encode()).hexdigest()[:8]
                    conflicts.append(VisionConflict(
                        conflict_id=cid,
                        type="DOMAIN_COLLISION",
                        involved_handoffs=[m.handoff_id for m in missions],
                        personas=p_involved,
                        description=f"Colisión de perspectiva en '{surface}': {len(missions)} misiones propuestas por {', '.join(p_involved)}.",
                        severity="medium",
                        suggested_arbitration="Fusionar misiones o secuenciar prioridades (Arquitecto prevalece en core)."
                    ))

        # 2. Method Tension (Auditor vs others)
        for h in handoffs:
            p_origin = getattr(h, "origin_persona", "CREATOR_CORE")
            if h.risk_level == "high" and p_origin != "AUDITOR":
                # Check if there's an Auditor mission for the same domain
                auditor_missions = [m for m in handoffs if getattr(m, "origin_persona", "CREATOR_CORE") == "AUDITOR"]
                if not any(set(h.surface_affected) & set(m.surface_affected) for m in auditor_missions):
                    cid = hashlib.md5(f"method:{h.handoff_id}".encode()).hexdigest()[:8]
                    conflicts.append(VisionConflict(
                        conflict_id=cid,
                        type="METHOD_CONFLICT",
                        involved_handoffs=[h.handoff_id],
                        personas=[p_origin, "AUDITOR"],
                        description=f"Alarma de Método: Misión de alto riesgo en '{h.surface_affected}' sin auditoría acompañante.",
                        severity="high",
                        suggested_arbitration="El AUDITOR recomienda añadir Hardening o Gate de validación antes de proceder."
                    ))

        return conflicts

    def arbitrate_by_constitution(self, conflict_id: str) -> Dict[str, Any]:
        """Uses constitutional rules to resolve conflicts."""
        conflicts = self.detect_vision_conflicts()
        c = next((x for x in conflicts if x.conflict_id == conflict_id), None)
        if not c: return {"error": "Conflict not found"}
        
        # Arbitrate by Role Weight
        p_weights = {p: self.personas.get(p, self.personas["CREATOR_CORE"]).weight for p in c.personas}
        winner = max(p_weights, key=p_weights.get)
        
        return {
            "winner": winner,
            "rationale": f"Resolución constitucional: Prevalece '{winner}' por peso operativo y jerarquía de rol.",
            "action": "PROMOTE_PRIORITY" if winner != "CREATOR_CORE" else "CORE_DECISION_PENDING"
        }

persona_sync = PersonaSyncManager()
