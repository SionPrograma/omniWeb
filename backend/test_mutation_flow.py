import asyncio
import json
import os
from backend.core.master_logbook.manager import master_logbook_manager
from backend.core.master_logbook.models import MasterLogbookEntry
from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.ai_host.execution.builder_engine import builder_execution_engine
from backend.core.ai_host.execution.builder_models import BuilderStatus
from backend.core.permissions import set_chip_context

async def test_mutation_flow():
    with set_chip_context("core"):
        print("\n--- 1. Creating Roadmap with Mutation Payload ---")
        roadmap_content = {
            "title": "Mutation Engine Test",
            "modules": [
                {
                    "title": "Batch Creation",
                    "type": "implementation",
                    "description": "Create two files and modify one",
                    "payload": {
                        "mutations": [
                            {"path": "tmp/mut_test_1.txt", "op_type": "CREATE_FILE", "content": "Hello 1"},
                            {"path": "tmp/mut_test_2.txt", "op_type": "CREATE_FILE", "content": "Hello 2"}
                        ]
                    }
                },
                {
                    "title": "Batch Failure & Rollback",
                    "type": "implementation",
                    "description": "This should fail and rollback",
                    "payload": {
                        "mutations": [
                            {"path": "tmp/mut_test_1.txt", "op_type": "MODIFY_FILE", "content": "Modified Content"},
                            {"path": "tmp/restricted_dir", "op_type": "CREATE_FILE", "content": "This will fail because it is a dir"}
                        ]
                    }
                }
            ]
        }
        
        entry = MasterLogbookEntry(
            type="roadmap",
            content=json.dumps(roadmap_content),
            priority="high",
            status="open"
        )
        entry_id = entry.id
        master_logbook_manager.add_entry(entry)
        print(f"Roadmap created: {entry_id}")

        print("\n--- 2. Approving ---")
        res = await ai_command_router.route(f"aprobá el roadmap {entry_id}")
        print(f"Approval response: {res.message}")
        
        # Give it a tiny bit of time to ensure persistence
        await asyncio.sleep(0.5)

        task_id = None
        # Check active tasks or database
        for tid, t in builder_execution_engine.active_tasks.items():
            if t.roadmap_id == entry_id:
                task_id = tid
                break
        
        if not task_id:
            # Fallback to DB
            import sqlite3
            conn = sqlite3.connect('backend/data/omniweb.db')
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT id FROM builder_tasks WHERE roadmap_id = ?", (entry_id,)).fetchone()
            if row:
                task_id = row['id']
            conn.close()

        print(f"Task ID Found: {task_id}")

        print("\n--- 3. Starting Execution ---")
        await builder_execution_engine.start_execution(task_id)

        print("\n--- 4. Monitoring Progress ---")
        for _ in range(15):
            task = await builder_execution_engine.get_task(task_id)
            print(f"Progress: {task.progress}% | Status: {task.status}")
            
            if task.status in [BuilderStatus.COMPLETED, BuilderStatus.FAILED]:
                break
            await asyncio.sleep(1)

        # Verification
        print("\n--- 5. Verification ---")
        # Check if first module succeeded
        if os.path.exists("tmp/mut_test_1.txt"):
            print("SUCCESS: tmp/mut_test_1.txt created")
            with open("tmp/mut_test_1.txt", "r") as f:
                content = f.read()
                print(f"Content: {content}")
        
        # Check if second module rolled back (mut_test_1 should still be "Hello 1")
        if os.path.exists("tmp/mut_test_1.txt"):
            with open("tmp/mut_test_1.txt", "r") as f:
                content = f.read()
                if content == "Hello 1":
                    print("SUCCESS: Rollback verified (content stayed 'Hello 1')")
                else:
                    print(f"FAILURE: Rollback failed (content is '{content}')")

if __name__ == "__main__":
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    asyncio.run(test_mutation_flow())
