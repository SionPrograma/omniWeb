import asyncio
import os
import sys
from backend.core.ai_host.execution.hot_reload import hot_reload_engine
from backend.core.permissions import set_chip_context

async def test_hot_reload():
    # Set environment
    os.environ["OMNIWEB_MODE"] = "creator"

    print("--- 1. Pre-import Check ---")
    module_name = "backend.core.ai_host.execution.system_auditor"
    
    # 1. Ensure module is loaded
    import backend.core.ai_host.execution.system_auditor
    print(f"Module {module_name} in sys.modules: {module_name in sys.modules}")
    
    # 2. Simulate file path
    file_path = "backend/core/ai_host/execution/system_auditor.py"
    
    print(f"\n--- 2. Triggering Hot Reload for {file_path} ---")
    with set_chip_context("core"):
        results = await hot_reload_engine.notify_changes([file_path])
    
    for res in results:
        print(f"Result: {res}")

    # 3. Test protection
    protected_path = "backend/core/database.py"
    print(f"\n--- 3. Testing Protection for {protected_path} ---")
    with set_chip_context("core"):
        results = await hot_reload_engine.notify_changes([protected_path])
    for res in results:
        print(f"Result: {res}")

    # 4. Simulate Failure
    from unittest.mock import patch
    print("\n--- 4. Testing Failure Handling ---")
    with patch("importlib.reload", side_effect=Exception("Simulated Reload Crash")):
        with set_chip_context("core"):
            results = await hot_reload_engine.notify_changes([file_path])
        for res in results:
            print(f"Result: {res}")

    # 5. Verify DB logging
    from backend.core.database import db_manager
    print("\n--- 5. Verifying DB Logs ---")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT module_name, status, timestamp FROM hot_reload_logs ORDER BY timestamp DESC LIMIT 5").fetchall()
            for row in rows:
                print(f"LOG: {row['module_name']} | {row['status']} | {row['timestamp']}")

if __name__ == "__main__":
    asyncio.run(test_hot_reload())
