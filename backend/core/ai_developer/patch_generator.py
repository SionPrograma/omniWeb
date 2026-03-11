import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class PatchGenerator:
    """
    Translates natural language modification requests into code patches.
    """
    def generate_patch(self, request: str, chip_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates patches for specific files based on instructions.
        """
        req = request.lower()
        patches = []
        
        # 1. Modify UI (Buttons, components)
        if any(x in req for x in ["boton", "button", "ui", "export", "pdf"]):
            target_html = next((f for f in chip_analysis["frontend"] if "index.html" in f or "main.html" in f), None)
            
            if target_html:
                if "pdf" in req or "export" in req:
                    btn_html = '\n<button id="export-pdf-btn" class="omni-btn-secondary"><i class="fas fa-file-pdf"></i> Export PDF</button>'
                    script_inject = '\n<script>document.getElementById("export-pdf-btn")?.addEventListener("click", () => alert("Exporting to PDF..."));</script>'
                    patches.append({
                        "file": target_html,
                        "action": "insert_before",
                        "target": "</body>",
                        "content": btn_html + script_inject,
                        "description": "Add PDF export functionality to UI"
                    })
                else:
                    patches.append({
                        "file": target_html,
                        "action": "insert_before",
                        "target": "</body>",
                        "content": '\n<button class="omni-btn-primary">New Action</button>',
                        "description": "Add generic button to UI"
                    })

        # 2. Add Backend Endpoints
        if any(x in req for x in ["endpoint", "route", "api"]):
            router_file = next((f for f in chip_analysis["backend"] if "router.py" in f), None)
            if router_file:
                # Basic name extraction
                route_name = "new-ai-endpoint"
                if "export" in req: route_name = "export-data"
                
                content = f'\n\n@router.post("/{route_name}")\nasync def {route_name.replace("-", "_")}():\n    # AI Generated logic\n    return {{"status": "success", "data": "AI processed request"}}\n'
                
                patches.append({
                    "file": router_file,
                    "action": "append",
                    "content": content,
                    "description": f"Added {route_name} endpoint to router"
                })

        # 3. Workflow Integration
        if "workflow" in req or "pasos" in req:
            router_file = next((f for f in chip_analysis["backend"] if "router.py" in f), None)
            if router_file:
                content = '\n\n# Workflow Integration\nfrom backend.core.workflows.workflow_engine import workflow_engine\n\n@router.post("/run-workflow")\nasync def run_chip_workflow(workflow_id: str):\n    return await workflow_engine.execute(workflow_id)\n'
                patches.append({
                    "file": router_file,
                    "action": "append",
                    "content": content,
                    "description": "Add workflow execution capability"
                })
                
        return patches

patch_generator = PatchGenerator()
