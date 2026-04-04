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

async def validate_feedback():
    print("--- VALIDATING MULTIMODAL CONTEXT FEEDBACK LOOP ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 0. RESET
        active = mission_manager.get_active_mission()
        if active:
            active.status = MissionStatus.COMPLETED
            mission_manager.save_mission(active)
            mission_manager._active_mission = None

        # 1. SETUP: Simular evidencia inicial archivada
        print("\n[STEP 1] Creating initial evidence to archive...")
        ctx_initial = {
            "multimodal_evidence": [{"id": "ev_001", "data": "historical_auth"}]
        }
        await processor.process("[VISUAL_EVIDENCE] Error de auth en el dashboard", context=ctx_initial)
        m = mission_manager.get_active_mission()
        snapshot_id = m.multimodal_history[-1]["id"]
        m.multimodal_history[-1]["hypothesis"] = {
            "layer": "backend/auth",
            "component": "Authenticator",
            "issue_type": "invalid_token",
            "description": "Fallo en la validacion de token visual"
        }
        mission_manager.save_mission(m)

        # 2. SHIFT: Archivar la primera
        print("\n[STEP 2] Shifting focus to archive...")
        await processor.process("[VISUAL_EVIDENCE] El login tiene un color equivocado", context={})

        # 3. TRIGGER RETRIEVAL: Volver a Auth
        print("\n[STEP 3] Triggering retrieval for auth...")
        await processor.process("[VISUAL_EVIDENCE] Revisar auth denuevo", context={})
        
        m = mission_manager.get_active_mission()
        # Verificar que esta pendiente o recuperada
        target_node = [h for h in m.multimodal_history if h.get("id") == snapshot_id][0]
        print(f"Memory Status after recall: {target_node.get('retrieval_metadata', {}).get('validation_status')}")

        # 4. REJECT: El creador rechaza la memoria (Falso positivo)
        print("\n[STEP 4] Creator REJECTS the memory recall...")
        success = m.validate_archival_recall(snapshot_id, approved=False, reason="Contexto cruzado: esto era de la sub-misión anterior")
        mission_manager.save_mission(m)
        
        if not success:
             raise Exception("FAILED: Validation action failed.")

        # 5. VERIFY RUNTIME EXCLUSION
        print("\n[STEP 5] Verifying runtime exclusion for agents...")
        m = mission_manager.get_active_mission()
        # El buscador la encontraria por relevancia técnica, pero get_compounded_context debe ignorarla
        ctx_for_agent = m.get_compounded_context(active_query={"layer": "backend/auth"})
        
        is_included = any(h.get("id") == snapshot_id for h in ctx_for_agent)
        print(f"Is rejected memory included in agent context? {is_included}")
        
        if is_included:
             raise Exception("FAILED: Rejected memory was still in agent context pool!")
             
        print(" - SUCCESS: Rejected memory surgically excluded from runtime.")

        # 6. REPORT VERIFICATION
        print("\n[STEP 6] Verifying visibility in Report...")
        report = multimodal_report_generator.generate_report(m.mission_id)
        report_node = [n for n in report["timeline"] if n.get("timestamp") == target_node.get("timestamp")][0]
        
        print(f"Report Node status: {report_node.get('retrieval_metadata', {}).get('validation_status')}")
        if report_node.get("retrieval_metadata", {}).get("validation_status") != "REJECTED":
             raise Exception("FAILED: Report does not reflect REJECTED status.")

        print("\n--- CONTEXT FEEDBACK LOOP VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_feedback())
