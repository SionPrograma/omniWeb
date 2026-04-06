import logging
import json
from typing import List, Dict, Any, Optional
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class ReplaySyncEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE STRATEGIC REPLAY LEDGER & AUTO-AUTOPSY SYNC.
    Closes the loop between Tactical Simulations and Real Outcomes.
    """
    def __init__(self):
        self.current_project_id = "PROJECT_OMNIWEB_PROD"

    async def synchronize_simulation_outcome(self, autopsy_id: str, branch_id: str) -> Optional[Dict[str, Any]]:
        """
        Links an autopsy back to its simulation (if any) and records alignment.
        """
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                # 1. Find if this branch was born from a simulation adoption
                ledger_res = await session.execute(
                    "SELECT ledger_id, rationale FROM governance_decision_ledger WHERE target_id = ? AND decision_type = 'ADOPTED_SIMULATED' LIMIT 1",
                    (branch_id,)
                )
                ledger = ledger_res.fetchone()
                if not ledger: return None # No simulation-based decision found for this branch
                
                # Extract simulation_id from rationale/target or separate field if added.
                # For Phase 301, we assumed the creator accepts from a simulation UI.
                # Let's search in simulation traces for this branch id.
                sim_trace_res = await session.execute(
                    "SELECT simulation_id, predicted_outcome, source_object_id FROM governance_tactical_simulations WHERE status = 'ADOPTED' AND simulation_id LIKE '%' || ? || '%' LIMIT 1",
                    (branch_id[:8],) # Heuristic if we didn't store the exact mapping
                )
                # Alternative: Check for any simulation that was marked as adopted recently.
                if not sim_trace_res:
                     # Fallback search by domain/type if no direct link
                    return None
                
                sim = sim_trace_res.fetchone()
                if not sim: return None
                
                # 2. Fetch Autopsy Outcome
                autopsy_res = await session.execute("SELECT * FROM governance_autopsies WHERE autopsy_id = ?", (autopsy_id,))
                autopsy = autopsy_res.fetchone()
                if not autopsy: return None
                
                # 3. Compare Predicted vs Actual
                # Metrics from Governance Autopsy (Fase 104)
                friction_relief = autopsy.get("friction_alleviation", 0)
                debt_reduction = autopsy.get("debt_reduction_score", 0)
                
                state = "PARTIALLY_CONFIRMED"
                delta = 0.0
                rationale = "El resultado real muestra un alivio moderado, alineado parcialmente con la simulación."
                
                if friction_relief > 25 or debt_reduction > 70:
                    if sim["predicted_outcome"] in ["LIKELY_RELIEF", "PARTIAL_RELIEF_EXPECTED"]:
                        state = "SIMULATION_CONFIRMED"
                        delta = 0.05
                        rationale = f"Simulación validada. El alivio real ({friction_relief}%) confirma la trayectoria proyectada."
                elif friction_relief < 5:
                    state = "CONTRADICTED_BY_REALITY"
                    delta = -0.1
                    rationale = f"Simulación fallida o desacoplada. Se predijo alivio pero el resultado real fue insuficiente ({friction_relief}%)."

                # 4. Save Sync Record
                sync_id = f"SYNC_{uuid.uuid4().hex[:8]}"
                await session.execute("""
                    INSERT INTO governance_replay_syncs (
                        sync_id, simulation_id, target_branch_id, autopsy_id,
                        predicted_effect, actual_outcome_summary, replay_outcome_state,
                        confidence_delta_proposed, rationale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sync_id, sim["simulation_id"], branch_id, autopsy_id,
                    sim["predicted_outcome"], f"Alivio: {friction_relief}%, Deuda: {debt_reduction}%",
                    state, delta, rationale
                ))
                
                return {"sync_id": sync_id, "state": state, "delta": delta, "rationale": rationale}

replay_sync_engine = ReplaySyncEngine()
