import sys
import os
import asyncio
import logging
import importlib

# Set up paths
sys.path.append(os.getcwd())

# Mock logging
logging.basicConfig(level=logging.INFO)

async def test_self_edit_workflow():
    from backend.core.permissions import _current_ctx_info
    _current_ctx_info.set({"chip_slug": "core", "user_id": "1"})
    
    from backend.core.ai_host.execution.mutation_engine import mutation_engine, MutationBatch, FileOperation, MutationType
    from backend.core.runtime.self_edit_runtime import self_edit_runtime
    from backend.core.database import db_manager

    # 1. Setup Dummy Module
    dummy_path = "tests_omni/self_edit_dummy.py"
    module_name = "tests_omni.self_edit_dummy"
    
    with open(dummy_path, "w") as f:
        f.write("DATA = 'original'\n")
    
    # Import it so HotReload tracks it
    import tests_omni.self_edit_dummy
    print(f"Initial DATA: {tests_omni.self_edit_dummy.DATA}")

    # 2. Setup DB dummy task (avoid FK error)
    TEST_TASK_ID = "self-edit-task"
    with db_manager.get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO builder_tasks (id, roadmap_id, title, status) VALUES (?, ?, ?, ?)", 
                     (TEST_TASK_ID, "roadmap", "Self Edit Test", "EXECUTING"))
        conn.commit()

    print("\n--- TEST A: SUCCESSFUL SELF-EDIT ---")
    batch_success = MutationBatch(
        task_id=TEST_TASK_ID,
        operations=[
            FileOperation(path=dummy_path, op_type=MutationType.MODIFY_FILE, content="DATA = 'modified'\n")
        ],
        origin="OmniTest"
    )
    
    success, reloads = await mutation_engine.execute_batch(batch_success)
    print(f"Mutation Success: {success}")
    print(f"Reload Results: {reloads}")
    
    with open(dummy_path, "r") as f:
        print(f"File content after success: {f.read().strip()}")

    # Explicitly check sys.modules
    import tests_omni.self_edit_dummy
    print(f"Updated DATA: {tests_omni.self_edit_dummy.DATA}")
    assert tests_omni.self_edit_dummy.DATA == 'modified'

    print("\n--- TEST B: FAILED SELF-EDIT (Syntax Error) -> ROLLBACK ---")
    # We backup the current 'modified' file
    original_content_before_failure = "DATA = 'modified'\n"
    
    batch_fail = MutationBatch(
        task_id=TEST_TASK_ID,
        operations=[
            FileOperation(path=dummy_path, op_type=MutationType.MODIFY_FILE, content="DATA = 'broken'\nSYNTAX_ERROR <<<")
        ],
        origin="OmniTest"
    )
    
    success_f, reloads_f = await mutation_engine.execute_batch(batch_fail)
    print(f"Mutation Success (should be False): {success_f}")
    print(f"Reload Results: {reloads_f}")
    
    # Check if file was rolled back
    with open(dummy_path, "r") as f:
        current_content = f.read()
    
    print(f"File content after rollback check: {current_content.strip()}")
    if not success_f and "modified" in current_content:
        print("SUCCESS: File rolled back correctly after reload failure.")
    else:
        print("FAIL: File was not rolled back or mutation succeeded unexpectedly.")

    # Cleanup
    if os.path.exists(dummy_path): os.remove(dummy_path)
    if os.path.exists(dummy_path + ".bak"): os.remove(dummy_path + ".bak")

if __name__ == "__main__":
    try:
        asyncio.run(test_self_edit_workflow())
    except Exception as e:
        print(f"TEST FAILED with error: {e}")
        import traceback
        traceback.print_exc()
