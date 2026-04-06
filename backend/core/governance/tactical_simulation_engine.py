import logging
import json
from typing import List, Dict, Any, Optional
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class TacticalSimulationEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE TACTICAL REPLAY & SIMULATION.
    Simulates the probable impact of reusing a past learning in the current live context.
    """
    def __init__(self):
        self.current_project_id = "PROJECT_OMNIWEB_PROD"

    async def run_tactical_simulation(self, source_type: str, source_id: str, target_domain: str = None) -> Dict[str, Any]:
        """
        Contrasts a past tactic against current live signals (friction, drift, ROI).
        """
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                # 1. Fetch Source Data
                source_obj = await self._fetch_source_object(session, source_type, source_id)
                if not source_obj: return {"error": "Source object not found"}
                
                # 2. Fetch Project Similarity (from Contextual Mapping)
                source_project_id = source_obj.get("project_id", "UNKNOWN")
                mapping_res = await session.execute(
                    "SELECT similarity_score FROM governance_contextual_mappings WHERE source_project_id = ? AND target_project_id = ?",
                    (source_project_id, self.current_project_id)
                )
                mapping = mapping_res.fetchone()
                project_similarity = mapping["similarity_score"] if mapping else 0.3 # Moderate default
                
                # 3. Analyze Current Target State
                # Check current friction in target domain
                current_f_res = await session.execute(
                    "SELECT friction FROM roadmap_branches WHERE target_domain = ? ORDER BY created_at DESC LIMIT 1",
                    (target_domain or source_obj.get("target_domain"),)
                )
                current_friction = current_f_res.fetchone()["friction"] if current_f_res.rowcount > 0 else 50.0
                
                # Check for structural resistance
                # (Assuming we have a table or engine for that)
                
                # 4. Simulation Logic
                confidence = 1.0 * project_similarity
                transfer_risk = 1.0 - project_similarity
                
                outcome = "PARTIAL_RELIEF_EXPECTED"
                rationale = "Similitud moderada entre proyectos."
                preconditions = ["Validar que no existan bloqueos técnicos de nivel 1 en el dominio."]
                
                # Heuristics
                if project_similarity > 0.8:
                    outcome = "LIKELY_STRUCTURAL_RELIEF"
                    rationale = f"Afinidad DNA muy alta ({int(project_similarity*100)}%). La táctica fue exitosa en un contexto idéntico."
                elif current_friction > 75:
                    outcome = "REQUIRES_RELIEF_FIRST"
                    rationale = "La presión actual en el dominio es crítica; aplicar una táctica optimizadora sin aliviar primero podría fallar."
                    preconditions.append("Lanzar misión de alivio (Relief Mission) previo al despliegue.")
                elif project_similarity < 0.4:
                    outcome = "HIGH_TRANSFER_RISK"
                    transfer_risk += 0.2
                    rationale = "Los proyectos son tácticamente distintos. Extrapolación de lecciones puede ser peligrosa."
                    
                # Store Simulation Result
                sim_id = f"SIM_{uuid.uuid4().hex[:8]}"
                sim_result = {
                    "simulation_id": sim_id,
                    "source_type": source_type,
                    "source_id": source_id,
                    "target_domain": target_domain or source_obj.get("target_domain"),
                    "predicted_outcome": outcome,
                    "confidence": round(confidence, 2),
                    "transfer_risk": round(min(1.0, transfer_risk), 2),
                    "rationale": rationale,
                    "preconditions": preconditions,
                    "contrast_factors": {
                        "project_similarity": project_similarity,
                        "current_friction": current_friction,
                        "source_confidence": source_obj.get("confidence", 0.5)
                    }
                }
                
                await session.execute("""
                    INSERT INTO governance_tactical_simulations (
                        simulation_id, source_object_type, source_object_id, target_domain,
                        predicted_outcome, confidence, transfer_risk, rationale,
                        contrast_factors, recommended_preconditions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sim_id, source_type, source_id, sim_result["target_domain"],
                    outcome, confidence, sim_result["transfer_risk"], rationale,
                    json.dumps(sim_result["contrast_factors"]), json.dumps(preconditions)
                ))
                
                return sim_result

    async def _fetch_source_object(self, session, source_type: str, source_id: str) -> Optional[Dict[str, Any]]:
        table_map = {
            "LEARNING": ("governance_learning_items", "learning_item_id"),
            "AUTOPSY": ("governance_autopsies", "autopsy_id"),
            "DECISION": ("governance_decision_ledger", "ledger_id")
        }
        if source_type not in table_map: return None
        table, id_col = table_map[source_type]
        res = await session.execute(f"SELECT * FROM {table} WHERE {id_col} = ?", (source_id,))
        return res.fetchone()

tactical_simulation_engine = TacticalSimulationEngine()
