import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "backend"))

def check_live_status():
    from backend.core.module_registry import module_registry
    
    chips = module_registry.discover_all_chips()
    idiomas_json = next((c for c in chips if c["slug"] == "idiomas"), None)
    print(f"JSON Discovery: {idiomas_json is not None}")
    
    # Check what is currently inside module_registry (Wait, the memory state is from another process...)
    # We can't access live memory of uvicorn from this script.
    
check_live_status()
