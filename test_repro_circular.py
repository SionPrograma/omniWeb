import sys
import os

# Ensure project root is in path
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

print("--- REPRODUCING CIRCULAR IMPORT ---")
try:
    # 1. Importing permissions first often triggers the chain
    # permissions -> creator_control -> database -> db_manager undefined?
    from backend.core.permissions import enforce_permission
    print("permissions imported")
    from backend.core.database import db_manager
    print("database imported")
    print(f"db_manager: {db_manager}")
    print(f"db_manager.get_session: {db_manager.get_session}")
except AttributeError as e:
    print(f"\nFAILED with AttributeError: {e}")
    # import traceback
    # traceback.print_exc()
except Exception as e:
    print(f"Other error: {e}")

print("\n--- REPRODUCING SYSTEM STATE ENGINE ---")
try:
    from backend.core.system_state.engine import state_engine
    print("state_engine imported")
    print(f"state_engine database info: {state_engine._get_sync_info('test_user')}")
except AttributeError as e:
    print(f"FAILED with AttributeError: {e}")
except Exception as e:
    print(f"Other error: {e}")
