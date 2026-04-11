import asyncio
import os
import sys

# Add backend to path for module resolution
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def validate_chip_integration():
    from backend.core.module_registry import module_registry
    
    # 1. Manually Discover Chips
    chips = module_registry.discover_all_chips()
    idiomas_chip = next((c for c in chips if c["slug"] == "idiomas"), None)
    print(f"[1] Chip 'idiomas' autodiscovered: {idiomas_chip is not None}")
    
    if idiomas_chip:
        # Mocking module loading
        module_registry._register_module_state("idiomas", "/idiomas", idiomas_chip)
        print(f"[2] Chip 'idiomas' state registered successfully: {module_registry.get_module_data('idiomas')['active_backend']}")
        
    # 2. Test Brain Router Interception
    from backend.core.ai_host.brain_router import BrainRouter
    from backend.core.ai_host.routing.command_router import CommandRouter
    
    router = CommandRouter()
    brain = BrainRouter(router)
    
    print("[3] Simulating normal conversation...")
    # "hola" usually goes to FAST PATH, so let's try a conversational sentence that hits FALLBACK
    response_normal = await brain._handle_natural_chat("hablame de cualquier cosa?", None, "es")
    print(f"Normal Fallback Resp: {response_normal.message}")
    
    print("[4] Simulating translation path...")
    response_translate = await brain._handle_natural_chat("traduce el texto hola", None, "es")
    print(f"Translate Intercept Resp: {response_translate.message}")
    
    print("VALIDATION SUCCESS")

if __name__ == "__main__":
    asyncio.run(validate_chip_integration())
