
import asyncio
import logging
import sys
import os

# Mocking setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.ai_host.shadow_swarm.approval_gate import approval_gate, GateStatus
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus
from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.routing.command_router import ai_command_router

logging.basicConfig(level=logging.INFO)

async def test_governance_synthesis():
    router = BrainRouter(ai_command_router)
    
    print("\n--- SETUP: Fresh Mission ---")
    mission = mission_manager.create_mission("Auditoria de Sintesis")
    
    # 1. Simulate drift alerts
    mission.context_snap["drift_alerts"] = [{
        "type": "CORE_BYPASS",
        "severity": "WARNING",
        "message": "Intento de acceso a core/security",
        "timestamp": "2026-04-02T03:30:00",
        "suggestion": "Revisar politicas"
    }]
    
    # 2. Simulate risk consumption
    mission.parameters["risk_consumed"] = 5.0
    mission.parameters["risk_budget"] = 10.0
    
    # 3. Check health (Guarded / Warning)
    health1 = approval_gate.get_governance_health(mission)
    print(f"Status 1: {health1['status']}")
    print(f"Rec 1: {health1['recommendation']}")
    assert health1['status'] == "DESVIACIÓN LEVE"

    # 4. Trigger EXTREME RISK (Priority shift)
    print("\n--- TRIGGER: Autonomy Limit ---")
    mission.parameters["risk_consumed"] = 11.0
    health2 = approval_gate.get_governance_health(mission)
    print(f"Status 2: {health2['status']}")
    assert health2['status'] == "AUTONOMÍA AGOTADA"

    # 5. Check Manual Command
    print("\n--- COMMAND: Request Manual ---")
    resp_manual = await router._handle_mission_adjustment("mostrame el manual de gobernanza")
    print(f"Response Intent: {resp_manual.intent}")
    print(f"Message slice:\n{resp_manual.message[:200]}...")
    assert "MANUAL DE GOBERNANZA" in resp_manual.message

    # 6. Verify auto-injection in save_mission
    print("\n--- ACTION: Save Mission and Verify Injection ---")
    mission_manager.save_mission(mission)
    # Reload
    reloaded = mission_manager.get_active_mission()
    print(f"Injected Health Status: {reloaded.context_snap.get('governance_health', {}).get('status')}")
    assert reloaded.context_snap.get('governance_health', {}).get('status') == "AUTONOMÍA AGOTADA"

    print("\n--- GOVERNANCE SÍNTESIS VALIDATED ---")

if __name__ == "__main__":
    asyncio.run(test_governance_synthesis())
