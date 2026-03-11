import json
import os

class ChipTemplates:
    """
    Provides scaffolds for different chip types.
    """
    
    @staticmethod
    def get_chip_json_template(spec) -> str:
        data = {
            "id": f"chip-{spec.slug}",
            "slug": spec.slug,
            "name": spec.name,
            "description": spec.description,
            "version": "1.0.0",
            "type": spec.type,
            "has_frontend": True,
            "has_backend": spec.type == "hybrid",
            "entry_frontend": "frontend/index.html",
            "dashboard_visible": True,
            "permissions": spec.permissions,
            "active": False,
            "installed": True,
            "created_by": "ai-host",
            "created_at": __import__("datetime").datetime.utcnow().isoformat()
        }
        return json.dumps(data, indent=4)

    @staticmethod
    def get_frontend_template(spec) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{spec.name}</title>
    <style>
        body {{ font-family: sans-serif; background: #111; color: #eee; padding: 2rem; }}
        .card {{ border: 1px solid #333; padding: 1rem; border-radius: 8px; background: #1a1a1a; }}
        button {{ background: #444; color: white; border: none; padding: 8px 16px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{spec.name} Chip</h1>
        <p>{spec.description}</p>
        <div id="content">Loading endpoints...</div>
    </div>
    <script>
        console.log("{spec.name} chip loaded.");
    </script>
</body>
</html>
"""

    @staticmethod
    def get_router_template(spec) -> str:
        endpoints_code = ""
        for ep in spec.endpoints:
            method, path = ep.split(" ")
            path = path.lower()
            method_name = method.lower()
            endpoints_code += f"""
@router.{method_name}("{path}")
def {method_name}_{path.replace('/', '_').strip('_')}() {{
    return {{"status": "ok", "message": "Endpoint {method} {path} works!"}}
}}
"""
        return f"""from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

{endpoints_code}
"""
