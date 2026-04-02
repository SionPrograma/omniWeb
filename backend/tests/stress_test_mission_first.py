import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.ai_host.memory.mission_manager import MissionManager, MissionStatus
from backend.core.ai_host.orchestration.prompt_compiler import prompt_compiler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("STRESS_TEST")

async def test_mission_first_hardening():
    print("\n" + "="*60)
    print("CORE STRESS TEST: MISSION-FIRST HARDENING & COMPILER")
    print("="*60 + "\n")

    mission_manager = MissionManager()
    
    # Ensure no active mission first
    active = mission_manager.get_active_mission()
    if active:
        mission_manager.set_status(MissionStatus.COMPLETED)
        mission_manager.active_mission = None

    # 1. TEST: Complex Megaprompt Compilation
    print(">>> STEP 1: LONG MEGAPROMPT COMPILATION")
    megaprompt = """
    MISIÓN: Hardening de la Seguridad del Swarm
    OBJETIVO: Auditar todos los puntos de entrada del Shadow Swarm y asegurar que el Approval Gate intercepte cada mutación.
    
    RESTRICCIONES:
    - No tocar los archivos de la base de datos central.
    - No modificar el sistema de logs existente.
    - Mantener retrocompatibilidad con la versión 1.2 del router.
    
    CRITERIOS DE ÉXITO:
    - Todas las llamadas a os.system deben estar prohibidas.
    - El gate debe registrar un ID único por cada intento de bypass.
    - El árbol de ejecución debe mostrar al menos 4 fases de validación.
    
    RIESGOS:
    - Latencia en el bus de comandos si el gate es muy pesado.
    - Falsos positivos en comandos del creador legítimos.
    """
    
    compiled = prompt_compiler.compile(megaprompt)
    print(f"Result: {compiled.mission_name}")
    print(f"Objective: {compiled.primary_objective[:50]}...")
    print(f"Layers: {compiled.target_surface}")
    print(f"Constraints Found: {len(compiled.constraints)}")
    print(f"Success Criteria: {len(compiled.success_criteria)}")
    print(f"Risks Detected: {len(compiled.risks_detected)}\n")
    
    if not compiled.is_ambiguous and len(compiled.constraints) >= 3:
        print("✅ COMPILER: PASS (Robust extraction confirmed)\n")
    else:
        print("❌ COMPILER: FAIL (Missing metadata or ambiguous)\n")

    # 2. TEST: Workspace Operational Continuity (The "Seguí" case)
    print(">>> STEP 2: WORKSPACE FOLLOW-UP PROTECTION")
    # Start a mission
    mission_manager.create_mission("Auditar Gate de Seguridad", pending_steps=["task1", "task2"])
    
    follow_ups = ["seguí", "arreglalo", "por qué", "y ahora", "reintentá", "aplicá eso"]
    
    for msg in follow_ups:
        res = await ai_command_router.route(msg, context={"source_surface": "workspace", "user_id": "test_creator"})
        # We expect a technical or mission intent, NOT 'chat'
        is_operational = res.intent in ["mission_followup", "mission_action", "creator_analysis", "creator_plan", "acknowledgment", "mission_status"]
        status_marker = "✅" if is_operational else "❌"
        print(f"{status_marker} Input: '{msg}' -> Intent: {res.intent} (Surface: Workspace)")
        
        # Verify mission is STILL OPEN
        active = mission_manager.get_active_mission()
        if active and active.status == MissionStatus.OPEN:
             print(f"   [MISSION STATUS]: OPEN (Shielded)")
        else:
             print(f"   [MISSION STATUS]: {active.status if active else 'None'} (FAILED TO SHIELD)")

    # 3. TEST: Public Shell Integrity (Casual Chat still works)
    print("\n>>> STEP 3: PUBLIC SHELL INTEGRITY")
    casual_inputs = ["hola", "cómo estás", "buen día"]
    for msg in casual_inputs:
        res = await ai_command_router.route(msg, context={"source_surface": "chat", "user_id": "test_user"})
        # MUST be 'chat' intent if no prefix
        is_chat = res.intent == "chat"
        status_marker = "✅" if is_chat else "❌"
        print(f"{status_marker} Input: '{msg}' -> Intent: {res.intent} (Surface: Chat)")

    # 4. TEST: Mission Actions (Cancel / Approve)
    print("\n>>> STEP 4: MISSION ACTIONS")
    
    # Cancel
    res_cancel = await ai_command_router.route("cancelá la misión", context={"source_surface": "workspace"})
    print(f"Cancel Input -> Intent: {res_cancel.intent}")
    
    # Approve
    res_approve = await ai_command_router.route("aprobado, aplicalo", context={"source_surface": "workspace"})
    print(f"Approve Input -> Intent: {res_approve.intent}")

    print("\n" + "="*60)
    print("FINAL REPORT GENERATED")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_mission_first_hardening())
