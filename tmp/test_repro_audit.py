import asyncio
import sys
import os
import importlib
import time

# Ensure the backend root is in sys.path
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)

from backend.core.ai_host.execution.hot_reload import hot_reload_engine

async def test_reload():
    file_path = "tests_omni/self_edit_dummy.py"
    
    # 1. Ensure it's loaded
    import tests_omni.self_edit_dummy as dummy
    old_val = getattr(dummy, "DATA", "NONE")
    print(f"Initial state: {old_val}")

    # 2. Modify to a new random value
    new_val = f"val_{int(time.time())}"
    with open(file_path, "w") as f:
        f.write(f"DATA = '{new_val}'\n")
    
    # 3. Trigger hot reload
    results = await hot_reload_engine.notify_changes([file_path])
    print(f"Reload Results: {results}")

    # 4. Verify
    print(f"Post-reload state: {dummy.DATA}")
    if dummy.DATA == new_val:
        print("SUCCESS: Module variable updated.")
    else:
        print(f"FAILURE: Expected {new_val}, got {dummy.DATA}")

if __name__ == "__main__":
    asyncio.run(test_reload())
