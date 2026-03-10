from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "active_modules": module_registry.get_active_modules()
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "omniweb-core"}

# Register active modules
# 1. Lingua module
module_registry.register_module(
    app=app,
    module_name="lingua",
    router_import_path="modules.lingua.api.lingua_routes.router",
    prefix="/api/v1/lingua"
)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
