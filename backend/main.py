from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core.config import settings
from backend.core.module_registry import module_registry
import uvicorn
import sys
import os

# Ensure the root of the project is in the Python path so we can import modules
sys.path.append(os.getcwd())

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def root():
    return FileResponse("frontend/dashboard/index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "omniweb-core"}

# Mount Core static resources
app.mount("/core", StaticFiles(directory="core"), name="core_static")

# Mount Modules UI & Register API Routes
for module_name in settings.ACTIVE_MODULES:
    # 1. Mount UI
    ui_path = None
    if module_name == "lingua":
        ui_path = "modules/lingua/ui"
    else:
        chip_folder = f"chip-{module_name}"
        ui_path = f"chips/{chip_folder}/frontend"
    
    if ui_path and os.path.exists(ui_path):
        app.mount(f"/{module_name}", StaticFiles(directory=ui_path, html=True), name=f"{module_name}_ui")
        print(f"Mounted UI for {module_name} at /{module_name}")

    # 2. Register API Router (if exists)
    router_path = None
    if module_name == "lingua":
        router_path = "modules.lingua.api.lingua_routes.router"
    else:
        # Expected pattern for new chips: chips.chip-name.core.router
        router_path = f"chips.chip-{module_name}.core.router"
        
    # Attempt registration (registry handles errors if path doesn't exist)
    module_registry.register_module(
        app=app,
        module_name=module_name,
        router_import_path=router_path,
        prefix=f"{settings.API_V1_STR}/{module_name}"
    )



if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
