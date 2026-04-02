import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus, MissionState
    from backend.core.ai_host.orchestration.execution_tree import tree_planner, ExecutionTree, NodeStatus
    from backend.core.ai_host.orchestration.prompt_compiler import prompt_compiler
    from backend.core.ai_host.routing.command_router import ai_command_router
except ImportError:
    print("WARNING: Could not import core components. Run with PYTHONPATH set.")
    import sys
    import os
    sys.path.append(os.getcwd())
    from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus, MissionState
    from backend.core.ai_host.orchestration.execution_tree import tree_planner, ExecutionTree, NodeStatus
    from backend.core.ai_host.orchestration.prompt_compiler import prompt_compiler
    from backend.core.ai_host.routing.command_router import ai_command_router

import asyncio

logging.basicConfig(level=logging.INFO)

def run_deep_audit():
    print("\n" + "="*50)
    print("OMNIWEB: DEEP MISSION AUDIT (RUNTIME)")
    print("="*50)

    # 1. TEST COMPILATION & TREE GENERATION
    print("\n>>> STEP 1: Compilación de Megaprompt complejo")
    megaprompt = """
    MISIÓN: Auditoría de Seguridad Core
    OBJETIVO: Revisar y endurecer los permisos de acceso al bus de datos.
    FLUJO: 
    1. Scan de permisos actuales.
    2. Modificar backend/core/data_bus.py.
    3. Validar integridad.
    RESTRICCIONES: No romper el flujo de producción.
    """
    
    compiled = prompt_compiler.compile(megaprompt)
    print(f"[OK] Compilado: {compiled.mission_name}")
    print(f"     Ambiguo: {compiled.is_ambiguous} ({compiled.ambiguity_notes})")
    
    tree = tree_planner.generate(compiled)
    print(f"[OK] Árbol generado con {len(tree.get_flat_tasks())} tareas.")
    
    # 2. TEST PERSISTENCE
    print("\n>>> STEP 2: Persistencia inicial")
    mission = mission_manager.create_mission(
        goal=compiled.primary_objective,
        plan_id=tree.mission_id,
        pending_steps=[t.label for t in tree.get_flat_tasks()],
        plan=tree # Pasamos el árbol para context_snap
    )
    print(f"[OK] Misión creada: {mission.mission_id}")
    print(f"     Status: {mission.status}")
    
    # 3. SIMULATE COMPLETION OF A STEP
    print("\n>>> STEP 3: Avance operativo")
    first_task = tree.get_flat_tasks()[0]
    print(f"     Completando tarea: {first_task.label}")
    first_task.status = NodeStatus.COMPLETED
    mission_manager.update_mission_step(first_task.label)
    
    # 4. TEST REHYDRATION (The Critical Point)
    print("\n>>> STEP 4: Rehidratación (Simulando reinicio)")
    # Limpiamos instancia en memoria (singleton)
    mission_manager.active_mission = None
    
    rehydrated = mission_manager.get_active_mission()
    if not rehydrated:
        print("[FAIL] No se recuperó ninguna misión activa.")
        return
    
    print(f"[OK] Misión rehidratada: {rehydrated.mission_id}")
    print(f"     Status: {rehydrated.status}")
    print(f"     Pasos completados: {len(rehydrated.completed_steps)}")
    
    # Check Tree in context_snap
    has_tree = "plan_data" in rehydrated.context_snap
    print(f"     ¿Tiene datos del árbol?: {has_tree}")
    
    if has_tree:
        tree_data = rehydrated.context_snap["plan_data"]
        # Verify if it's a full tree or just a summary
        # If it's a dict from model_dump, we should check for 'root'
        is_full_tree = "root" in tree_data
        print(f"     ¿Es árbol completo?: {is_full_tree}")
        
        if is_full_tree:
            print(f"     [VERDE] La persistencia del árbol es íntegra.")
        else:
            print(f"     [AMARILLO] Persistencia parcial detectada.")
    else:
        print(f"     [ROJO] PÉRDIDA DE CONTEXTO TÉCNICO: El árbol no se persistió en context_snap.")

    # 5. TEST CROSS-COMPONENT ALIGNMENT
    print("\n>>> STEP 5: Alineación de capas")
    # Detect follow-up in active mission context
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(ai_command_router.route("seguí", context={"source_surface": "workspace"}))
    print(f"     Input 'seguí' -> Intent: {response.intent}")
    
    if "mission" in response.intent:
        print("     [VERDE] El Router reconoce la continuidad operativa.")
    else:
        print(f"     [ROJO] Desconexión de Router: No reconoce misiones activas (Intent: {response.intent}).")

    print("\n" + "="*50)
    print("AUDIT COMPLETE")
    print("="*50)

if __name__ == "__main__":
    run_deep_audit()
