import asyncio
import sys
import os
import importlib

# Ensure the backend root is in sys.path
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)

from backend.core.ai_host.execution.hot_reload import hot_reload_engine

async def test_syntax_error():
    file_path = "tests_omni/self_edit_dummy.py"
    
    # 1. Clean file and load it
    with open(file_path, "w") as f:
        f.write("DATA = 'clean'\n")
    
    import tests_omni.self_edit_dummy as dummy
    print(f"Loaded module. Current state: {dummy.DATA}")

    # 2. Write invalid python code
    with open(file_path, "w") as f:
        f.write("DATA = 'error'\nINVALID PYTHON CODE HERE >>>\n")
    
    # 3. Trigger hot reload (it's in sys.modules now)
    results = await hot_reload_engine.notify_changes([file_path])
    print(f"Reload Results for syntax error (Expected FAILED): {results}")

    # 4. Confirm it failed in DB
    import sqlite3
    conn = sqlite3.connect('backend/data/omniweb.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM hot_reload_logs WHERE status='FAILED' ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"Latest FAILED log in DB: {dict(row)}")
    else:
        print("No FAILED log found in DB.")
    conn.close()

if __name__ == "__main__":
    asyncio.run(test_syntax_error())
