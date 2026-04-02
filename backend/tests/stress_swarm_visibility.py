import asyncio
import os
import sys
import logging
from typing import Dict, Any

# Setup PYTHONPATH
sys.path.append(os.getcwd())

from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.shadow_swarm.shadow_constructor import shadow_constructor_manager
from backend.core.system_state.engine import state_engine
from backend.core.ai_host.shadow_swarm.approval_gate import approval_gate
from backend.core.permissions import set_chip_context

logging.basicConfig(level=logging.INFO)

async def stress_test_swarm():
    print("\n" + "="*50)
    print("STRESS TEST: SWARM VISIBILITY & PERSISTENCE")
    print("="*50)

    with set_chip_context("core"):
        # 1. Lanzo una misión
        print("\n>>> STEP 1: Iniciando misión compleja")
        mission = mission_manager.create_mission(
            goal="Optimización de seguridad en el bus de datos core.",
            plan_id="stress-mission-001",
            pending_steps=["Auditar permisos", "Aplicar parche", "Verificar"]
        )
        print(f"[OK] Misión: {mission.mission_id}")

        # 2. Activo el Swarm (Constructor)
        print("\n>>> STEP 2: Activando Swarm Constructor")
        constructor = shadow_constructor_manager.spawn_constructor(
            mission_id=mission.mission_id,
            microtask="Mejorar validación de JWT en el bus",
            layer="backend/core",
            file="backend/core/data_bus.py"
        )
        # Draft proposal
        proposal = await constructor.draft_proposal()
        print(f"[OK] Propuesta generada: {constructor.shadow_id}")
        print(f"     Diff: {proposal.diff_preview}")

        # 3. Evaluar por Approval Gate
        print("\n>>> STEP 3: Evaluación de Gobernanza")
        decision = approval_gate.evaluate_proposal(constructor)
        print(f"[OK] Decisión del Gate: {decision.status} (Nivel: {decision.danger_level})")

        # 4. Verificar visibilidad en SystemState
        print("\n>>> STEP 4: Verificación de visibilidad en SystemState")
        state = await state_engine.get_state(force_refresh=True)
        
        # Check if proposals field exists
        state_dict = state.model_dump()
        has_proposals_field = "proposals" in state_dict
        print(f"     ¿Campo 'proposals' existe en SystemState?: {has_proposals_field}")
        
        proposals_count = len(state_dict.get("proposals", []))
        print(f"     ¿Hay propuestas en el estado?: {proposals_count}")

        # 5. REFRESH (Simulated)
        print("\n>>> STEP 5: Simulación de Refresh (Limpieza de caché)")
        # Clear cache in engine
        state_engine._state = None
        state_engine._last_update = 0
        
        refreshed_state = await state_engine.get_state(force_refresh=True)
        refreshed_dict = refreshed_state.model_dump()
        
        proposals_after_refresh = len(refreshed_dict.get("proposals", []))
        print(f"     Propuestas tras refresh: {proposals_after_refresh}")

    # 6. RESULTADO
    print("\n" + "="*50)
    print("RESULTADOS DEL TEST")
    print("="*50)
    
    if not has_proposals_field:
        print("[ROJO] CAMPO FALTANTE: SystemState no soporta 'proposals'.")
    elif proposals_count == 0:
        print("[AMARILLO] DESCONEXIÓN: El Swarm no inyecta propuestas en el motor de estado.")
    elif proposals_after_refresh > 0:
        print("[VERDE] PERSISTENCIA OK: El Swarm es visible y persistente tras refresh.")
    else:
        print("[AMARILLO] VOLATILIDAD: Las propuestas se pierden al refrescar el estado.")

    print("="*50)

if __name__ == "__main__":
    asyncio.run(stress_test_swarm())
