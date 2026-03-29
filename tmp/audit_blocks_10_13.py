
import asyncio
import logging
import sys
import os

# Add project root to sys.path
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

# Configure logging to see the execution
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("AUDIT")

from backend.core.ai_host.shadow_swarm.shadow_orchestrator import shadow_orchestrator
from backend.core.ai_host.shadow_swarm.shadow_constructor import ConstructorState
from backend.core.ai_host.shadow_swarm.approval_gate import GateStatus

async def run_scenario(name, goal, force_apply=False):
    print(f"\n=== SCENARIO: {name} ===")
    print(f"Goal: {goal}")
    context = {"session_id": "audit_test", "force_apply": force_apply}
    try:
        result = await shadow_orchestrator.execute_mission(goal, context)
        print(f"Status: {result['status']}")
        print(f"Jobs Executed: {result['jobs_executed']}")
        
        for c in result.get('constructors', []):
            print(f"Constructor {c['shadow_id']} state: {c['state']}")
            if 'apply_record' in c.get('context', {}):
                print(f"  Apply Record: {c['context']['apply_record']['verification']}")
        
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

async def main():
    # Scenario 1: Low risk mission
    await run_scenario("Safe Mission", "Optimizar el manejo de errores en core/module.py")
    
    # Scenario 2: Critical mission (Sensitive layer)
    # The gate should escalate or block this
    await run_scenario("Critical Mission", "Modificar el sistema de permisos en core/permissions")
    
    # Scenario 3: Manual Apply with force
    await run_scenario("Manual Apply", "Actualizar documentación interna", force_apply=True)

if __name__ == "__main__":
    asyncio.run(main())
