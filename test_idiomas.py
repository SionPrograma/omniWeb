import importlib

print("Testing importlib...")
try:
    mod = importlib.import_module("chips.chip-idiomas.core.services.language_engine")
    import asyncio
    msg = asyncio.run(mod.language_engine.enhance_natural_chat("traduce hola", None, "es"))
    print(f"SUCCESS: {msg}")
except Exception as e:
    import traceback
    traceback.print_exc()
