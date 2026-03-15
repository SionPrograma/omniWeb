import asyncio
import sys
import os

# Ensure project root is in path
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

async def test():
    print("--- TESTING SYSTEM STATE ENGINE REAL FLOW ---")
    try:
        from backend.core.system_state.engine import state_engine
        print("state_engine imported successfully.")
        
        # Test the update cycle (which calls cluster_manager etc.)
        # We'll use a local bypass to avoid the DB permission denial for the test
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            state = await state_engine.get_state(force_refresh=True)
            print(f"System State retrieved: Version {state.version}")
            print(f"Database connected: {state.database['connected']}")
            print(f"Health: {state.health}")
            print(f"Cluster Info: {state.cluster}")
            
        print("\n--- TEST RESULT: SUCCESS ---")
    except AttributeError as e:
        print(f"\nFAILED with AttributeError: {e}")
    except Exception as e:
        print(f"\nFAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
