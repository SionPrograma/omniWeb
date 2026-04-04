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
from backend.core.ai_host.processors.multimodal_report import multimodal_report_generator

async def validate_retrieval():
    print("--- VALIDATING MULTIMODAL SEMANTIC RETRIEVAL ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SETUP: Simular evidencia inicial sobre AUTH
        print("\n[STEP 1] Creating initial evidence (AUTH focus)...")
        ctx_auth = {
            "multimodal_evidence": [{"id": "ev_001", "data": "auth_visual"}]
        }
        # Inyectamos una hipótesis manual para simular que el procesador detectó AUTH
        res1 = await processor.process("[VISUAL_EVIDENCE] El login no funciona", context=ctx_auth)
        m = mission_manager.get_active_mission()
        # Forzar tipado manual para asegurar match futuro
        m.multimodal_history[-1]["hypothesis"] = {
            "layer": "backend/auth",
            "component": "LoginController",
            "issue_type": "permission_denied",
            "description": "Fallo en validación de JWT"
        }
        mission_manager.save_mission(m)
        print(f"Auth focus recorded and archived.")

        # 2. SHIFT: Mover el foco a UI (Esto archiva lo de AUTH)
        print("\n[STEP 2] Shifting focus to UI (Archiving AUTH)...")
        ctx_ui = {
            "multimodal_evidence": [{"id": "ev_002", "data": "ui_visual"}]
        }
        await processor.process("[VISUAL_EVIDENCE] El color del boton es feo", context=ctx_ui)
        m = mission_manager.get_active_mission()
        # Verificar que AUTH es SUPPORT ahora
        auth_entry = [h for h in m.multimodal_history if "auth" in str(h.get("hypothesis",{}).get("layer"))][0]
        print(f"Initial AUTH entry relevance: {auth_entry.get('relevance')}")

        # 3. RETRIEVAL TRIGGER: El creador vuelve a mencionar AUTH
        print("\n[STEP 3] Creator points back to AUTH (Triggering Retrieval)...")
        ctx_back_auth = {
            "multimodal_evidence": [{"id": "ev_003", "data": "auth_visual_2"}]
        }
        # Simulamos una re-orientación que coincide técnicamente con la primera
        response = await processor.process("[VISUAL_EVIDENCE] Espera, volvamos al problema del JWT en backend/auth", context=ctx_back_auth)
        
        print(f"Response Message: {response.message}")
        
        # 4. VERIFY RECOVERY
        print("\n[STEP 4] Verifying recovery in MissionState...")
        m = mission_manager.get_active_mission()
        
        # Check if the recovered metadata exists in history
        has_retrieval = any(h.get("retrieval_metadata") is not None for h in m.multimodal_history)
        print(f"Any history item has retrieval_metadata? {has_retrieval}")
        
        # Check compounded context (what agents see)
        # Simulamos que un agente pregunta por el contexto actual de backend/auth
        comp_context = m.get_compounded_context(active_query={"layer": "backend/auth"})
        
        recovered_items = [h for h in comp_context if h.get("relevance") == "RECOVERED"]
        print(f"Compounded context size: {len(comp_context)}")
        print(f"Recovered items found for agent: {len(recovered_items)}")
        
        if not has_retrieval or len(recovered_items) == 0:
             raise Exception("FAILED: Archive Retrieval not working!")

        print(f"Match Reason: {recovered_items[0]['retrieval_metadata']['match_reason']}")
        print(" - SUCCESS: Semantic retrieval identified relevant archive.")

        # 5. REPORT VALIDATION
        print("\n[STEP 5] Verifying Report Exposure...")
        report = multimodal_report_generator.generate_report(m.mission_id)
        found_in_report = any(node.get("retrieval_metadata") for node in report["timeline"])
        print(f"Recovery visible in Report? {found_in_report}")
        
        if not found_in_report:
             raise Exception("FAILED: Retrieval metadata missing in report!")

        print("\n--- SEMANTIC RETRIEVAL VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_retrieval())
