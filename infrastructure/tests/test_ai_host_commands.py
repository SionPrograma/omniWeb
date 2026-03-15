import asyncio
import os
import sys
import shutil

# Ensure path
sys.path.append(os.getcwd())

from backend.core.ai_host.command_router import ai_command_router
from backend.core.module_registry import module_registry

async def test_ai_commands():
    print("\n--- Testing AI Host Commands ---")
    
    # 1. Test Open Chip
    resp = await ai_command_router.route("Abrir finanzas")
    print(f"Open Finanzas: {resp}")
    assert resp.intent == "open_chip"
    assert resp.status == "success"
    assert resp.payload["target"] == "finanzas"
    print("   [PASS] Open chip intent recognized.")

    # 2. Test List Chips
    resp = await ai_command_router.route("Listar mis chips")
    print(f"List Chips: {resp}")
    assert resp.intent == "list_chips"
    assert "reparto" in resp.message.lower() or "finanzas" in resp.message.lower()
    print("   [PASS] List chips intent recognized.")

    # 3. Test Create Chip (Call real factory but cleanup)
    target_slug = "custom-tasks"
    if os.path.exists(f"chips/chip-{target_slug}"):
        shutil.rmtree(f"chips/chip-{target_slug}")
        
    resp = await ai_command_router.route("Crea un chip de tareas")
    print(f"Create Tasks: {resp}")
    assert resp.intent == "create_chip"
    assert resp.status == "success"
    assert os.path.exists(f"chips/chip-{target_slug}")
    print("   [PASS] Create chip integrated with factory.")
    
    shutil.rmtree(f"chips/chip-{target_slug}")

    # 4. Test System Status
    resp = await ai_command_router.route("¿Cual es el estado del sistema?")
    print(f"Status: {resp}")
    assert resp.intent == "system_status"
    print("   [PASS] System status intent recognized.")

if __name__ == "__main__":
    asyncio.run(test_ai_commands())
