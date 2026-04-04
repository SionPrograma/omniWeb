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

async def validate_refocus():
    print("--- VALIDATING MULTIMODAL CONTEXT RE-FOCUS (MANUAL) ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 0. RESET
        active = mission_manager.get_active_mission()
        if active:
            active.status = MissionStatus.COMPLETED
            mission_manager.save_mission(active)
            mission_manager._active_mission = None

        # 1. SETUP: Simular evidencia archivada que fue RECHAZADA (Gobernanza extrema)
        print("\n[STEP 1] Creating archived evidence and rejecting it first...")
        ctx_initial = {
            "multimodal_evidence": [{"id": "ev_001", "data": "old_ux_bug"}]
        }
        await processor.process("[VISUAL_EVIDENCE] El boton esta mal alineado", context=ctx_initial)
        m = mission_manager.get_active_mission()
        snapshot_id = m.multimodal_history[-1]["id"]
        
        # Simular rechazo previo
        m.validate_archival_recall(snapshot_id, approved=False, reason="No relevante aun")
        mission_manager.save_mission(m)

        # 2. SHIFT: Archivar
        await processor.process("[VISUAL_EVIDENCE] Otro tema irrelevante", context={})

        # 3. MANUAL REACTIVATION: El creador decide que SI es relevante ahora
        print("\n[STEP 2] Manual reactivation (Override)...")
        m = mission_manager.get_active_mission()
        success = m.reactivate_archival_snapshot(snapshot_id, active=True, reason="Necesito esta referencia visual ahora")
        mission_manager.save_mission(m)
        
        if not success:
             raise Exception("FAILED: Manual reactivation logic failed.")

        # 4. VERIFY RUNTIME RE-INJECTION
        print("\n[STEP 3] Verifying runtime re-injection (Priority check)...")
        m = mission_manager.get_active_mission()
        
        # El compounded context debe incluirlo por MANUAL_REACTIVATION a pesar de haber sido REJECTED historicamente
        ctx_for_agent = m.get_compounded_context(active_query={"layer": "frontend/ui"})
        
        target = next((h for h in ctx_for_agent if h.get("id") == snapshot_id), None)
        
        if not target:
             raise Exception("FAILED: Reactivated memory missing from compounded context.")
             
        print(f"Node Relevance: {target.get('relevance')}")
        print(f"Agent Summary: {target.get('impact_summary')}")
        
        if target.get("relevance") != "MANUAL_REACTIVATION":
             raise Exception("FAILED: Incorrect relevance tag for manual reactivation.")

        # 5. VERIFY OVERRIDE IN METADATA
        validation_status = target.get("retrieval_metadata", {}).get("validation_status")
        print(f"Validation Override Status: {validation_status}")
        if validation_status != "VALIDATED":
             raise Exception("FAILED: Manual reactivation did not override previous rejection.")

        print("\n--- CONTEXT RE-FOCUS VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_refocus())
