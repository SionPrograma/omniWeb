try:
    print("Testing import: backend.core.cluster.manager")
    from backend.core.cluster.manager import cluster_manager
    print("Success: cluster_manager imported.")
    
    print("Testing cluster_manager.get_cluster_state()")
    import asyncio
    async def run():
        await cluster_manager.get_cluster_state()
    asyncio.run(run())
    print("Success: cluster_manager.get_cluster_state() executed.")
except AttributeError as e:
    print(f"FAILED with AttributeError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"FAILED with other error: {e}")
    # traceback.print_exc()
