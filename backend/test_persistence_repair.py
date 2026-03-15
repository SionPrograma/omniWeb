import sys
import asyncio
import logging

# Add backend to path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

logging.basicConfig(level=logging.INFO)

async def test_persistence():
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    
    print("--- 1. Testing get_session() async context manager ---")
    try:
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                print("Session opened successfully.")
                cursor = await session.execute("SELECT 1 as val")
                row = cursor.fetchone()
                print(f"Query Result: {row['val']}")
                print("PASS: get_session() and execute() working.")
    except Exception as e:
        print(f"FAIL: {e}")

    print("\n--- 2. Testing ClusterManager (Uses get_session) ---")
    try:
        from backend.core.cluster.manager import cluster_manager
        # This will call get_cluster_state which uses get_session
        with set_chip_context("core"):
            state = await cluster_manager.get_cluster_state()
            print(f"Cluster State: {state.active_nodes} active nodes.")
            print("PASS: ClusterManager integration working.")
    except Exception as e:
        print(f"FAIL: {e}")

    print("\n--- 3. Testing SystemStateEngine (The original crash site) ---")
    try:
        from backend.core.system_state.engine import state_engine
        with set_chip_context("core"):
            state = await state_engine.get_state(force_refresh=True)
            print(f"System Health: {state.health}")
            print(f"Uptime: {state.uptime_seconds}s")
            print("PASS: SystemStateEngine recovered.")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(test_persistence())
