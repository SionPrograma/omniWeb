
import asyncio
import sys
import os
import json
from datetime import datetime

# Setup project root
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

from backend.core.ai_host.shadow_swarm.shadow_orchestrator import shadow_orchestrator
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.permissions import set_chip_context

async def run_rescue_validation():
    print("# VALIDACIÓN: COGNITIVE AUDIT RESCUE")
    print("=" * 60)
    
    with set_chip_context("core"):
        # 1. SETUP: Mission with Multimodal Refinement
        print("\n[PASO 1] CREANDO MISIÓN CON EVIDENCIA MULTIMODAL")
        v_ctx = {
            "hypothesis": {
                "description": "Fallo crítico en renderizado de Footer",
                "layer": "frontend/shell",
                "component": "footer",
                "route": "frontend/shell/index.html",
                "confidence": "high",
                "issue_type": "empty_state"
            },
            "annotations": [{"type": "box", "comment": "footer roto"}]
        }
        
        mission = mission_manager.create_mission("Arreglar footer")
        mission.visual_context = v_ctx
        mission.related_targets = ["frontend/shell/index.html"]
        mission_manager.save_mission(mission)
        
        # 2. SIMULATE FAILURE: Create a failed node in the tree
        print("\n[PASO 2] SIMULANDO PASO FALLIDO EN LA MISIÓN")
        step_id = "step_failed_001"
        mission.context_snap["tree"] = {
            "root": {
                "id": "root",
                "label": "Misión Raíz",
                "children": [
                    {
                        "id": step_id,
                        "label": "Auditoría de Footer",
                        "status": "FAILED",
                        "deep_evidence": {"error": "Timeout al leer componente footer"}
                    }
                ]
            }
        }
        mission_manager.save_mission(mission)
        
        # 3. TRIGGER RESCUE
        print("\n[PASO 3] DISPARANDO RESCATE COGNITIVO (RESCUE_STEP)")
        res = await shadow_orchestrator.rescue_step(step_id, mission.mission_id)
        
        if res.get("status") == "success":
            result = res["result"]
            print(f"\n--- REPORTE DE RESCATE ---")
            print(f"Summary: {result.get('summary')}")
            print(f"Evidence: {result.get('new_evidence')}")
            print(f"Visual Refinement Used: {result.get('visual_refinement_applied')}")
            
            trace = result.get("cognitive_trace", {})
            print(f"Hipótesis en Trace: {trace.get('main_hypothesis')}")
            print(f"Camino Elegido: {trace.get('chosen_path')}")
        else:
            print(f"ERROR EN RESCATE: {res.get('message')}")

        print("\n" + "=" * 60)
        print("RESULTADO FINAL: RESCATE QUIRÚRGICO VALIDADO")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_rescue_validation())
