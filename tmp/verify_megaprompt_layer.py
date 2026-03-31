import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.ai_host.orchestration.prompt_compiler import prompt_compiler
from backend.core.ai_host.orchestration.execution_tree import tree_planner
from backend.core.ai_host.orchestration.scope_lock import DeviationDetector, ScopeLock

async def test_megaprompt_layer():
    megaprompt = """
    MISIÓN: Refactorizar la capa de persistencia de misiones.
    OBJETIVO: Migrar el almacenamiento de JSON plano a una estructura relacional más robusta en backend/core/database.
    SUPERFICIE: backend/core, backend/core/database
    PROHIBIDO: No tocar la capa de UI frontend/workspace.
    
    PASOS:
    1. Auditar core/database.py
    2. Modificar mission_manager.py
    """
    
    print("\n--- [1] Testing Prompt Compiler ---")
    compiled = prompt_compiler.compile(megaprompt)
    print(f"Mission: {compiled.mission_name}")
    print(f"Objective: {compiled.primary_objective}")
    print(f"Files Detected: {compiled.critical_files}")
    print(f"Forbidden: {compiled.forbidden_layers}")
    
    if "backend" in compiled.target_surface and "frontend/workspace" in str(compiled.forbidden_layers):
        print("PASS: Metadata extraction successful.")
    else:
        print("FAIL: Metadata extraction failed.")

    print("\n--- [2] Testing Execution Tree ---")
    tree = tree_planner.generate(compiled)
    print(f"Root: {tree.root.label}")
    print(f"Phases: {[c.label for c in tree.root.children]}")
    if len(tree.root.children) >= 3:
        print("PASS: Tree generated with Phases.")
    else:
        print("FAIL: Tree generation failed.")

    print("\n--- [3] Testing Scope Lock ---")
    lock = ScopeLock(compiled)
    
    # Valid action
    res_valid = lock.validate_action("mutation", "backend/core/database.py", "Actualizar esquema")
    print(f"Action 'backend/core/database.py': {'PASS' if res_valid['is_valid'] else 'FAIL'}")
    
    # Invalid action (Forbidden Zone)
    res_invalid = lock.validate_action("mutation", "frontend/workspace/main.js", "Cambiar color botón")
    print(f"Action 'frontend/workspace/main.js': {'FAIL' if res_valid['is_valid'] else 'PASS'} (Blocked as forbidden)")
    
    # Invalid action (Scope Creep)
    res_creep = lock.validate_action("mutation", "backend/core/ai_host/chat.py", "Ya que estamos, arreglo este bug")
    print(f"Action 'Scope Creep': {'FAIL' if res_creep['is_valid'] else 'PASS'} (Blocked as creep)")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_megaprompt_layer())
