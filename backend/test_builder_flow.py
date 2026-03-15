import asyncio
import json
import uuid
from backend.core.master_logbook.manager import master_logbook_manager
from backend.core.master_logbook.models import EntryType, Priority
from backend.core.ai_host.execution.builder_engine import builder_execution_engine
from backend.core.ai_host.routing.command_router import ai_command_router

from backend.core.permissions import set_chip_context

async def test_builder_flow():
    with set_chip_context("core"):
        print("--- 1. Creating Dummy Roadmap in Logbook ---")
        roadmap_data = {
            "title": "System Expansion Roadmap",
            "modules": [
                {
                    "title": "Module A: Initialization",
                    "type": "initialization",
                    "description": "Scaffold the project structure",
                    "payload": {"project_title": "OmniExp", "modules": ["core", "utils"]}
                },
                {
                    "title": "Module B: Core Logic",
                    "type": "implementation",
                    "description": "Implement the core processing loop",
                    "payload": {"context": "high performance"}
                },
                {
                    "title": "Module C: Integrity Check",
                    "type": "audit",
                    "description": "Perform full system audit"
                }
            ]
        }
        
        from backend.core.master_logbook.models import EntryType, Priority, MasterLogbookEntry
        
        entry = MasterLogbookEntry(
            type=EntryType.ROADMAP,
            content=json.dumps(roadmap_data),
            priority=Priority.HIGH
        )
        master_logbook_manager.add_entry(entry)
        print(f"Roadmap entry created: {entry.id}")

        print("\n--- 2. Approving Roadmap via CommandRouter ---")
        res = await ai_command_router.route("aprobá el roadmap")
        print(f"Intent: {res.intent}, Status: {res.status}, Message: {res.message}")
        task_id = res.payload.get("task_id")

        if task_id:
            print(f"\n--- 3. Starting Execution ---")
            exe_res = await ai_command_router.route("empezá la ejecución")
            print(f"Intent: {exe_res.intent}, Status: {exe_res.status}, Message: {exe_res.message}")
            
            print("\n--- 4. Monitoring Progress (Simulated) ---")
            for _ in range(10):
                await asyncio.sleep(2)
                task = builder_execution_engine.active_tasks.get(task_id)
                if task:
                    print(f"Progress: {task.progress}% | Current Mod: {task.current_module_id} | Status: {task.status}")
                    if task.status in ["COMPLETED", "FAILED", "CANCELLED"]:
                        break
        else:
            print("FAILED: Task ID not generated.")

if __name__ == "__main__":
    asyncio.run(test_builder_flow())
