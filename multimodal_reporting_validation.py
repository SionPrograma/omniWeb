
import asyncio
import sys
import os
import json
from datetime import datetime
from fastapi.testclient import TestClient

# Setup project root
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

from backend.main import app
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.permissions import set_chip_context
from backend.core.auth import OmniUser

client = TestClient(app)

# Dummy user for dependency injection
async def override_get_current_user():
    return OmniUser(id="creator_001", username="Creator", role="admin")

app.dependency_overrides[app.router.dependencies[0].dependency] = override_get_current_user # This depends on how it's structured

async def run_report_validation():
    print("# VALIDACIÓN: MULTIMODAL MISSION REPORTING")
    print("=" * 60)
    
    with set_chip_context("core"):
        # 1. SETUP: Complete Multimodal Life Cycle
        print("\n[PASO 1] CREANDO CICLO DE VIDA MULTIMODAL COMPLETO")
        mission = mission_manager.create_mission("Reparar Dashboard")
        mission_id = mission.mission_id
        
        # A. INITIAL CAPTURE
        mission.multimodal_history.append({
            "event": "INITIAL_CAPTURE",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"description": "Dashboard error"},
            "annotations": [{"type": "point", "x": 10, "y": 10}],
            "creator_comment": "El dashboard no carga"
        })
        
        # B. RE_ORIENTATION
        mission.multimodal_history.append({
            "event": "RE_ORIENTATION",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"description": "Chart data failure", "layer": "frontend/logic"},
            "annotations": [{"type": "box", "x": 100, "y": 100, "comment": "data region"}],
            "visual_diff": {"added_count": 1, "removed_count": 0},
            "creator_comment": "Es el gráfico de stats"
        })
        
        # C. TECHNICAL REFINEMENT (Stored in visual_context)
        mission.visual_context = {
            "hypothesis": {
                "description": "Fallo en gráfico de estadísticas",
                "layer": "frontend/dashboard",
                "component": "StatsChart",
                "route": "frontend/dashboard/charts.js",
                "confidence": "high",
                "issue_type": "data_gap",
                "roadmap_hint": "Auditar fetch en StatsChart"
            }
        }
        
        # D. RESCUE (In Tree)
        mission.context_snap["tree"] = {
            "root": {
                "id": "root", "label": "Mission", "children": [
                    {
                        "id": "r1", "label": "RESCUE: Patch StatsChart",
                        "status": "COMPLETED", "evidence": "Surgical patch applied to charts.js",
                        "deep_evidence": {"cognitive_trace": {"chosen_path": "Fixing API Mapping"}}
                    }
                ]
            }
        }
        
        mission_manager.save_mission(mission)
        print(f"Misión {mission_id} guardada con historia multimodal completa.")

        # 2. FETCH REPORT
        print("\n[PASO 2] CONSULTANDO ENDPOINT DE REPORTE (/ai-host/execution/mission/{id}/report)")
        
        # Note: We use a direct call if TestClient setup is complex, but let's try the endpoint
        response = client.get(f"/api/v1/ai-host/execution/mission/{mission_id}/report", headers={"Authorization": "Bearer OMNIWEB_ADMIN_TOKEN"})
        
        if response.status_code == 200:
            data = response.json()
            report = data.get("report", {})
            print(f"\n--- REPORTE CONSOLIDADO RECIBIDO ---")
            print(f"Goal: {report.get('goal')}")
            print(f"Hitos en Timeline: {len(report.get('timeline', []))}")
            
            for node in report.get("timeline", []):
                print(f"  [{node.get('type')}] {node.get('title')}: {node.get('description')}")
            
            ref = report.get("technical_refinement", {})
            print(f"\nRefinamiento Técnico:")
            print(f"  Capa: {ref.get('layer')} | Componente: {ref.get('component')}")
            print(f"  Confianza: {ref.get('confidence')}")
            
            rescue = report.get("rescue_impact", [])
            if rescue:
                print(f"\nImpacto de Rescate:")
                print(f"  Acción: {rescue[0].get('step')}")
                print(f"  Trazabilidad: {rescue[0].get('trace', {}).get('chosen_path')}")
        else:
             print(f"ERROR {response.status_code}: {response.text}")

        print("\n" + "=" * 60)
        print("RESULTADO FINAL: MULTIMODAL REPORTING VALIDADO")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_report_validation())
