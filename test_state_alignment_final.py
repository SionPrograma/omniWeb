import os
import sys
import json
import shutil
import asyncio
from fastapi import FastAPI, APIRouter

# Paths
CHIPS_DIR = "chips"
def get_chip_path(slug): return os.path.join(CHIPS_DIR, f"chip-{slug}")

def setup_chips():
    # 1. Healthy Core/Router
    c1 = "healthy_core"
    os.makedirs(os.path.join(get_chip_path(c1), "core"), exist_ok=True)
    with open(os.path.join(get_chip_path(c1), "chip.json"), "w") as f:
        json.dump({"id": f"chip-{c1}", "slug": c1, "name": "Healthy Core", "has_backend": True, "active": True}, f)
    with open(os.path.join(get_chip_path(c1), "core", "router.py"), "w") as f:
        f.write("from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/test')\ndef t(): return 1")

    # 2. Healthy Backend/Router
    c2 = "healthy_backend"
    os.makedirs(os.path.join(get_chip_path(c2), "backend"), exist_ok=True)
    with open(os.path.join(get_chip_path(c2), "chip.json"), "w") as f:
        json.dump({"id": f"chip-{c2}", "slug": c2, "name": "Healthy Backend", "has_backend": True, "active": True}, f)
    with open(os.path.join(get_chip_path(c2), "backend", "router.py"), "w") as f:
        f.write("from fastapi import APIRouter\nrouter = APIRouter()")

    # 3. Missing Router (claims backend but file doesn't exist)
    c3 = "missing_router"
    os.makedirs(get_chip_path(c3), exist_ok=True)
    with open(os.path.join(get_chip_path(c3), "chip.json"), "w") as f:
        json.dump({"id": f"chip-{c3}", "slug": c3, "name": "Missing Router", "has_backend": True, "active": True}, f)

    # 4. Import Failure (Syntax Error)
    c4 = "import_failure"
    os.makedirs(os.path.join(get_chip_path(c4), "core"), exist_ok=True)
    with open(os.path.join(get_chip_path(c4), "chip.json"), "w") as f:
        json.dump({"id": f"chip-{c4}", "slug": c4, "name": "Import Failure", "has_backend": True, "active": True}, f)
    with open(os.path.join(get_chip_path(c4), "core", "router.py"), "w") as f:
        f.write("raise SyntaxError('Boom')")

def cleanup():
    for c in ["healthy_core", "healthy_backend", "missing_router", "import_failure"]:
        path = get_chip_path(c)
        if os.path.exists(path): shutil.rmtree(path)

async def validate():
    sys.path.append(os.getcwd())
    from backend.core.module_registry import module_registry
    from backend.core.system_state.engine import state_engine
    from backend.core.permissions import set_chip_context
    from backend.core.config import settings
    app = FastAPI()
    
    chips_to_test = [
        ("healthy_core", "chips.chip-healthy_core.core.router"),
        ("healthy_backend", "chips.chip-healthy_backend.backend.router"),
        ("missing_router", "chips.chip-missing_router.core.router"),
        ("import_failure", "chips.chip-import_failure.core.router")
    ]
    
    print("\nStarting Registration Sequence...")
    for slug, path in chips_to_test:
        print(f"-> Processing {slug}...")
        try:
            # Replicate main.py logic exactly
            if os.path.exists(path.replace(".", "/") + ".py") or os.path.exists(path.replace(".", "/").replace("core", "backend") + ".py"):
                 module_registry.register_module(app, slug, path, prefix=f"/api/v1/{slug}")
            else:
                 # Missing file case
                 module_registry._register_module_state(slug, None, {"slug": slug, "has_backend": True, "active": True})
        except Exception as e:
            print(f"   [!] CRITICAL ERROR in {slug}: {e}")
            module_registry._register_module_state(slug, None, {"slug": slug, "has_backend": True, "active": True})

    print("\n--- FINAL STATE ENGINE AUDIT ---")
    with set_chip_context("core"):
        state = await state_engine.get_state(force_refresh=True)
    
    results = []
    for c in state.chips:
        if c.slug in [s for s, _ in chips_to_test]:
            results.append({
                "slug": c.slug,
                "status": c.status,
                "health": c.health
            })
    
    print(json.dumps(results, indent=2))
    
    # Assertions
    expected = {
        "healthy_core": ("active", "healthy"),
        "healthy_backend": ("active", "healthy"),
        "missing_router": ("unloaded_backend", "warning"),
        "import_failure": ("unloaded_backend", "warning")
    }
    
    all_pass = True
    for r in results:
        exp_status, exp_health = expected[r["slug"]]
        if r["status"] == exp_status and r["health"] == exp_health:
            print(f"CHECK PASS: {r['slug']}")
        else:
            print(f"CHECK FAIL: {r['slug']} (Got {r['status']}/{r['health']}, expected {exp_status}/{exp_health})")
            all_pass = False
    
    if all_pass:
        print("\nSUMMARY: TRUTH ALIGNMENT SUCCESSFUL.")
    else:
        print("\nSUMMARY: TRUTH ALIGNMENT FAILED.")

if __name__ == "__main__":
    try:
        setup_chips()
        asyncio.run(validate())
    finally:
        cleanup()
