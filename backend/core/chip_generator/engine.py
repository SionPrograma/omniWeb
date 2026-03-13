import threading
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChipGenerator:
    """
    Scaffolding engine for OmniWeb Chips.
    Phase 13-14: Dynamic Chip Creation & Stabilization.
    """
    
    def __init__(self, base_dir: str = "chips"):
        self.base_dir = base_dir
        self._lock = threading.Lock()
        self._max_simultaneous = 1 # v1 limit
        self._active_generations = 0

    def create_chip(self, slug: str, name: Optional[str] = None) -> Dict[str, Any]:
        from backend.core.permissions import enforce_permission, CHIP_GENERATION_ACCESS
        enforce_permission(CHIP_GENERATION_ACCESS)
        with self._lock:
            if self._active_generations >= self._max_simultaneous:
                raise RuntimeError("Too many simultaneous chip generation requests. Please wait.")
            self._active_generations += 1
        
        try:
            return self._execute_scaffold(slug, name)
        finally:
            with self._lock:
                self._active_generations -= 1

    def _execute_scaffold(self, slug: str, name: Optional[str] = None) -> Dict[str, Any]:
        if not name:
            name = slug.replace("_", " ").capitalize()
            
        chip_folder = f"chip-{slug}"
        # Ensure base_dir is relative to project root
        target_path = os.path.join(self.base_dir, chip_folder)
        
        if os.path.exists(target_path):
            raise FileExistsError(f"Chip {slug} already exists at {target_path}")
            
        # 1. Create folders
        os.makedirs(os.path.join(target_path, "frontend"), exist_ok=True)
        os.makedirs(os.path.join(target_path, "backend"), exist_ok=True)
        
        # 2. Create chip.json
        metadata = {
            "id": f"chip-{slug}",
            "slug": slug,
            "name": name,
            "description": f"Módulo dinámico: {name}",
            "version": "0.1.0",
            "type": "hybrid",
            "has_frontend": True,
            "has_backend": True,
            "entry_frontend": "frontend/index.html",
            "active": True
        }
        
        with open(os.path.join(target_path, "chip.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
        # 3. Create frontend scaffold
        frontend_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>
        body {{
            background: #0a0c14;
            color: #fff;
            font-family: 'Inter', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }}
        .scaffold-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            max-width: 400px;
        }}
        h1 {{ margin: 0; color: #00d4ff; font-size: 2rem; }}
        p {{ color: #888; font-size: 0.9rem; margin: 10px 0; }}
        .status-badge {{
            display: inline-block;
            margin-top: 20px;
            padding: 5px 15px;
            background: #00ff88;
            color: #000;
            border-radius: 50px;
            font-weight: bold;
            font-size: 12px;
            letter-spacing: 1px;
        }}
        .system-info {{
            margin-top: 20px;
            font-size: 11px;
            color: #444;
        }}
    </style>
</head>
<body>
    <div class="scaffold-card">
        <h1>{name}</h1>
        <p>OmniWeb Dynamic Chip Scaffold</p>
        <div class="status-badge">ONLINE</div>
        <div class="system-info">Powered by OmniWeb Creator Engine</div>
    </div>
</body>
</html>
"""
        with open(os.path.join(target_path, "frontend/index.html"), "w", encoding="utf-8") as f:
            f.write(frontend_html)
            
        # 4. Create backend scaffold
        backend_py = f"""from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
async def get_status():
    return {{
        "chip": "{slug}",
        "status": "active",
        "message": "Backend for {name} is alive"
    }}
"""
        with open(os.path.join(target_path, "backend/router.py"), "w", encoding="utf-8") as f:
            f.write(backend_py)
            
        # 5. Empty __init__.py files for imports
        with open(os.path.join(target_path, "__init__.py"), "w", encoding="utf-8") as f:
            f.write("")
        with open(os.path.join(target_path, "backend/__init__.py"), "w", encoding="utf-8") as f:
            f.write("")

        logger.info(f"Successfully generated chip: {slug} at {target_path}")
        return {
            "slug": slug,
            "path": target_path,
            "metadata": metadata
        }

chip_generator = ChipGenerator()
