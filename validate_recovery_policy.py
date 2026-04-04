import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_recovery_policy():
    print("--- VALIDATING MISSION RECOVERY AUTO-EXECUTION POLICY ---")
    
    with set_chip_context("core"):
        # ----------------------------------------------------
        # CASO 1: AUTO-SAFE (Whitelisted + High Trust)
        # ----------------------------------------------------
        print("\n[SCENARIO 1] AUTO-EXECUTED: Whitelisted action + Support")
        # Inyectamos lección para RESTORE_EXECUTION_CONTEXT
        mission_manager.learning_engine.record_strategic_lesson(
            "recovery-manual", "TACTIC_SUCCESS", "ui/dashboard", 
            "La restauración de contexto es siempre segura en esta capa.",
            evidence="Manual audit", conf=0.98
        )
        
        m1 = mission_manager.create_mission("Re-orient UI Dashboard")
        # Forzar un estado que genere RESTORE_EXECUTION_CONTEXT en mitigación si es simulación
        # Pero nuestra whitelist en evaluate_recovery_auto_policy es lo que manda.
        # Vamos a mockear un escenario en m1 para el test
        
        print("       Simulating rehydration for AUTO-SAFE mission...")
        # Mocking generate_mitigation_scenarios to return a whitelisted safe action
        m1.multimodal_history.append({"event": "SIGNAL", "layer": "ui/dashboard", "confidence": 0.95})
        
        # Trigger rehydration logic
        mission_manager.active_mission = None
        # In memory rehydration simulates loading m1
        mission_manager.rehydrate_active_mission()
        
        mRec1 = mission_manager.get_active_mission()
        rec1 = mRec1.last_recovery
        pol1 = rec1.get("policy_decision", {})
        
        print(f"       Action: {rec1['suggested_path']['action'] if rec1['suggested_path'] else 'None'}")
        print(f"       Policy Level: {pol1.get('level')}")
        print(f"       Auto-Executed: {pol1.get('auto_executed', False)}")
        if pol1.get('auto_executed'):
             print(f"       ✅ SUCCESS: Safe micro-action executed autonomously.")
        else:
             print(f"       ❌ FAILED: Should have been auto-executed.")

        # ----------------------------------------------------
        # CASO 2: PRUDENCE (High Drift)
        # ----------------------------------------------------
        print("\n[SCENARIO 2] SUGGESTED ONLY: High Drift (>40)")
        m2 = mission_manager.create_mission("Uncertain Background Task")
        # Inyectamos deriva alta mediante un evento de cambio de foco
        m2.multimodal_history.append({"event": "INITIAL_CAPTURE", "hypothesis": {"layer": "ui/old"}})
        m2.multimodal_history.append({"event": "RE_ORIENTATION", "hypothesis": {"layer": "ui/new_experimental"}, "relevance": "SIGNAL"})
        
        mission_manager.save_mission(m2)
        mission_manager.active_mission = None
        mission_manager.rehydrate_active_mission()
        
        mRec2 = mission_manager.get_active_mission()
        rec2 = mRec2.last_recovery
        pol2 = rec2.get("policy_decision", {})
        
        print(f"       Drift On Recovery: {rec2['drift_on_recovery']}")
        print(f"       Policy Level: {pol2.get('level')}")
        if not pol2.get('auto_executed'):
             print(f"       ✅ SUCCESS: High drift kept it as suggestion only.")
        else:
             print(f"       ❌ FAILED: Auto-executed despite high drift.")

        # ----------------------------------------------------
        # CASO 3: BLOCKED (Sensitive Layer + High Focus Shift)
        # ----------------------------------------------------
        print("\n[SCENARIO 3: BLOCKED (Sensitive Layer)]")
        m3 = mission_manager.create_mission("Kernel Emergency Recovery")
        m3.multimodal_history.append({"event": "INITIAL_CAPTURE", "hypothesis": {"layer": "backend/core"}})
        m3.multimodal_history.append({"event": "RE_ORIENTATION", "hypothesis": {"layer": "backend/core/kernel"}, "relevance": "CRITICAL"})
        
        mission_manager.save_mission(m3)
        mission_manager.active_mission = None
        mission_manager.rehydrate_active_mission()
        
        mRec3 = mission_manager.get_active_mission()
        rec3 = mRec3.last_recovery
        pol3 = rec3.get("policy_decision", {})
        
        print(f"       Action: {rec3['suggested_path']['action'] if rec3['suggested_path'] else 'None'}")
        print(f"       Policy Level: {pol3.get('level')}")
        if pol3.get('level') == "CREATOR_REQUIRED":
             print(f"       ✅ SUCCESS: Sensitive action blocked auto-execution.")
        else:
             print(f"       ❌ FAILED: Should be blocked.")

    print("\n--- RECOVERY POLICY VALIDATION FINISHED ---")

if __name__ == "__main__":
    asyncio.run(validate_recovery_policy())
