import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.handoff_manager import handoff_manager

logger = logging.getLogger(__name__)

class TacticalOpportunity(BaseModel):
    opportunity_id: str
    type: str # REBASE_HOTSPOT, CONFLICT_CLUSTER, GOVERNANCE_FRICTION, ROLLBACK_PRONE, BACKLOG_NOISE
    surface: str
    score: float
    rationale: str
    evidence_summary: str
    suggested_mission: Dict[str, Any]
    status: str = "OPEN" # OPEN, ACCEPTED, IGNORED, ARCHIVED
    created_at: datetime = Field(default_factory=datetime.now)

class OpportunityScanner:
    """
    OMNIWEB — BLOQUE: TACTICAL OPPORTUNITY SCANNER.
    Detects friction patterns in the system and suggests proactive missions.
    """
    
    def scan_for_opportunities(self) -> List[TacticalOpportunity]:
        opportunities = []
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. REBASE HOTSPOTS (High density of mutants/rebases in builder_mutations)
                # Note: builder_mutations uses 'module_id' and REAL timestamp (unix epoch)
                hotspots = conn.execute("""
                    SELECT module_id, COUNT(*) as rebase_count 
                    FROM builder_mutations 
                    WHERE timestamp > (strftime('%s', 'now') - 86400)
                    GROUP BY module_id
                    HAVING rebase_count >= 3
                """).fetchall()
                
                for row in hotspots:
                    surface = row["module_id"]
                    count = row["rebase_count"]
                    
                    import hashlib
                    opp_id = hashlib.sha256(f"REBASE_HOTSPOT:{surface}".encode()).hexdigest()[:12]
                    
                    opportunities.append(TacticalOpportunity(
                        opportunity_id=opp_id,
                        type="REBASE_HOTSPOT",
                        surface=surface,
                        score=min(1.0, count / 10.0),
                        rationale=f"La superficie '{surface}' ha experimentado {count} mutaciones externas en las últimas 24h, forzando múltiples rebases tácticos.",
                        evidence_summary=f"Detectadas {count} mutaciones en builder_mutations.",
                        suggested_mission={
                            "objective": f"Refactorizar y aislar dependencias en '{surface}' para reducir la sensibilidad a cambios externos.",
                            "surface_affected": [surface],
                            "risk_level": "medium",
                            "constraints": ["No romper compatibilidad con módulos dependientes"]
                        }
                    ))

                # 2. GOVERNANCE FRICTION (Blocked steps in pushes)
                gates = conn.execute("""
                    SELECT payload, COUNT(*) as block_count 
                    FROM atomic_push_forensics 
                    WHERE event_type = 'STEP_BLOCKED' 
                    AND timestamp > datetime('now', '-48 hours')
                    GROUP BY payload
                """).fetchall()
                
                for row in gates:
                    payload = json.loads(row["payload"])
                    reason = payload.get("reason", "Unknown")
                    authority = payload.get("authority", "Unknown")
                    count = row["block_count"]
                    
                    if count >= 2:
                        import hashlib
                        opp_id = hashlib.sha256(f"GOVERNANCE_FRICTION:{authority}".encode()).hexdigest()[:12]
                        
                        opportunities.append(TacticalOpportunity(
                            opportunity_id=opp_id,
                            type="GOVERNANCE_FRICTION",
                            surface="global",
                            score=min(1.0, count / 5.0),
                            rationale=f"Fricción recurrente en Gate Analyzer: {count} misiones bloqueadas recientemente por {authority}.",
                            evidence_summary=f"Razón recurrente: {reason}",
                            suggested_mission={
                                "objective": f"Ajustar políticas de gobernanza para {authority} o implementar pre-autorización para misiones nominales.",
                                "surface_affected": ["governance_logic"],
                                "risk_level": "low",
                                "constraints": ["Mantener trazabilidad forense"]
                            }
                        ))

                # 3. ROLLBACK PRONE (Surfaces involved in reverts)
                rollbacks = conn.execute("""
                    SELECT handoff_id, COUNT(*) as revert_count 
                    FROM atomic_push_forensics 
                    WHERE event_type = 'ROLLBACK_STEP_COMPLETED'
                    GROUP BY handoff_id
                """).fetchall()
                
                for row in rollbacks:
                    h_id = row["handoff_id"]
                    count = row["revert_count"]
                    if count >= 1:
                        h = handoff_manager.get_proposal(h_id)
                        surface = h.surface_affected[0] if h and h.surface_affected else "unknown"
                        import hashlib
                        opp_id = hashlib.sha256(f"ROLLBACK_PRONE:{surface}".encode()).hexdigest()[:12]
                        
                        opportunities.append(TacticalOpportunity(
                            opportunity_id=opp_id,
                            type="ROLLBACK_PRONE",
                            surface=surface,
                            score=0.8,
                            rationale=f"La superficie '{surface}' ha requerido reversiones tácticas. Esto indica inestabilidad o falta de pruebas en el despliegue atómico.",
                            evidence_summary=f"Misión {h_id[:6]} revertida exitosamente.",
                            suggested_mission={
                                "objective": f"Implementar Hardening de estabilidad en '{surface}' y añadir validaciones post-push.",
                                "surface_affected": [surface],
                                "risk_level": "high",
                                "constraints": ["Asegurar rollback instantáneo si falla el hardening"]
                            }
                        ))

        # Filter duplicates/spam (simple surface/type key)
        unique_opps = {}
        for op in opportunities:
            key = (op.type, op.surface)
            if key not in unique_opps or op.score > unique_opps[key].score:
                unique_opps[key] = op
                
        return list(unique_opps.values())

    def convert_to_mission(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Converts an opportunity into a proposed mission in the handoff queue."""
        # Note: In a real system we'd store opportunities in DB. 
        # For this block, we'll re-scan and find by ID or use a temporary cache.
        opps = self.scan_for_opportunities()
        opp = next((o for o in opps if o.opportunity_id == opportunity_id), None)
        
        if not opp: return None
        
        # Add to handoff manager
        mission = handoff_manager.add_proposal(opp.suggested_mission, source="opportunity_scanner")
        return mission.model_dump()

opportunity_scanner = OpportunityScanner()
