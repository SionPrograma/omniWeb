import sys
import os
import json
import uuid
from datetime import datetime

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_deep_search():
    print("--- VALIDATING MULTIMODAL DEEP ARCHIVE SEARCH ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 0. RESET
        active = mission_manager.get_active_mission()
        if active:
            active.status = MissionStatus.COMPLETED
            mission_manager.save_mission(active)
            mission_manager._active_mission = None

        # 1. SETUP: Crear historial variado
        print("\n[STEP 1] Generating varied mission history...")
        
        # Evidencia 1: Error de Auth en Backend
        await processor.process("[VISUAL_EVIDENCE] Fallo de token en login", context={})
        m = mission_manager.get_active_mission()
        m.multimodal_history[-1]["hypothesis"] = {
            "layer": "backend/auth",
            "issue_type": "security_token_expired",
            "description": "El token de sesion ha expirado prematuramente"
        }
        m.multimodal_history[-1]["creator_comment"] = "Reportado por el equipo de QA"
        
        # Evidencia 2: Error de Color en CSS/Frontend
        await processor.process("[VISUAL_EVIDENCE] El boton es naranja en vez de verde", context={})
        m.multimodal_history[-1]["hypothesis"] = {
            "layer": "frontend/ui",
            "issue_type": "style_mismatch",
            "description": "Inconsistencia de colores en el componente Button"
        }
        
        # Evidencia 3: Error de Persistencia
        await processor.process("[VISUAL_EVIDENCE] No se guardan los cambios", context={})
        m.multimodal_history[-1]["hypothesis"] = {
            "layer": "backend/db",
            "issue_type": "write_failure",
            "description": "Fallo en la persistencia de datos"
        }
        mission_manager.save_mission(m)

        # 2. SEARCH BY TEXT: "token"
        print("\n[STEP 2] Searching by text: 'token'...")
        results_text = m.search_multimodal_archive(query="token")
        print(f"Found {len(results_text)} results.")
        for r in results_text:
            print(f" - [{r.get('id')[:8]}] Score: {r.get('search_score')} | Comment: {r.get('creator_comment')} | Layer: {r.get('hypothesis', {}).get('layer')}")
            
        if not any("token" in str(r).lower() for r in results_text):
             raise Exception("FAILED: Text search did not find mentioned token.")

        # 3. SEARCH BY LAYER FILTER: "backend/db"
        print("\n[STEP 3] Searching by layer filter: 'backend/db'...")
        results_db = m.search_multimodal_archive(filters={"layer": "backend/db"})
        print(f"Found {len(results_db)} results.")
        for r in results_db:
             print(f" - [{r.get('id')[:8]}] Layer: {r.get('hypothesis', {}).get('layer')} | Desc: {r.get('hypothesis', {}).get('description')}")

        if len(results_db) != 1 or results_db[0]["hypothesis"]["layer"] != "backend/db":
             raise Exception("FAILED: Layer filter incorrect.")

        # 4. SEARCH BY ISSUE TYPE: "style"
        print("\n[STEP 4] Searching by issue type: 'style'...")
        results_style = m.search_multimodal_archive(filters={"issue_type": "style"})
        print(f"Found {len(results_style)} results.")
        if not results_style or "style" not in results_style[0]["hypothesis"]["issue_type"]:
             raise Exception("FAILED: Issue type filter incorrect.")

        print("\n--- DEEP ARCHIVE SEARCH VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_deep_search())
