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

async def validate_explainability():
    print("--- VALIDATING MULTIMODAL COGNITIVE EXPLAINABILITY ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 0. RESET: Ensure no carry-over from previous tests
        active = mission_manager.get_active_mission()
        if active:
            active.status = MissionStatus.COMPLETED
            mission_manager.save_mission(active)
            mission_manager._active_mission = None

        # 1. SETUP: Simular evidencia inicial archivada
        print("\n[STEP 1] Creating initial evidence to archive...")
        ctx_initial = {
            "multimodal_evidence": [{"id": "ev_001", "data": "initial_data"}]
        }
        await processor.process("[VISUAL_EVIDENCE] Fallo en el modulo de persistence", context=ctx_initial)
        m = mission_manager.get_active_mission()
        m.multimodal_history[-1]["hypothesis"] = {
            "layer": "backend/persistence",
            "component": "DBAdapter",
            "issue_type": "write_timeout",
            "description": "El adapter de base de datos esta tardando mas de lo normal",
            "roadmap_hint": "Optimizar pool de conexiones"
        }
        mission_manager.save_mission(m)

        # 2. SHIFT: Mover el foco a otro lado para archivar el primero
        print("\n[STEP 2] Shifting focus to archive the initial one...")
        ctx_other = {
            "multimodal_evidence": [{"id": "ev_002", "data": "other_data"}]
        }
        await processor.process("[VISUAL_EVIDENCE] El icono del dashboard es incorrecto", context=ctx_other)

        # 3. TRIGGER RETRIEVAL WITH IMPACT: El creador vuelve a la persistencia
        print("\n[STEP 3] Triggering retrieval for persistence...")
        ctx_back = {
            "multimodal_evidence": [{"id": "ev_003", "data": "back_to_db"}]
        }
        await processor.process("[VISUAL_EVIDENCE] Siguen los fallos en backend/persistence", context=ctx_back)
        
        # 4. VERIFY COGNITIVE IMPACT
        print("\n[STEP 4] Verifying cognitive impact trace...")
        m = mission_manager.get_active_mission()
        print(f"Mission ID: {m.mission_id}")
        print(f"History Size: {len(m.multimodal_history)}")
        
        # Encontrar el ítem recuperado (debe tener retrieval_metadata y cognitive_impact)
        recovered_entry = None
        for i, h in enumerate(m.multimodal_history):
            hyp = h.get("hypothesis", {})
            print(f"Node {i} (Event: {h.get('event')}): Layer={hyp.get('layer')} Relevance={h.get('relevance')}")
            if h.get("retrieval_metadata") and h.get("retrieval_metadata").get("cognitive_impact"):
                recovered_entry = h
                print(f"Found Recovery at Node {i}!")
                break
        
        if not recovered_entry:
             raise Exception("FAILED: Cognitive impact trace not found in history!")
             
        impact = recovered_entry["retrieval_metadata"]["cognitive_impact"]
        print(f"Strategic Influence: {impact['reinforced_strategy']}")
        print(f"Historical Insight: {impact['historical_insight']}")
        print(f"Influence Level: {impact['influence']}")
        
        if "backend/persistence" not in impact["reinforced_strategy"]:
             raise Exception("FAILED: Impact explanation does not match recalled context.")

        print(" - SUCCESS: Strategic influence correctly traced.")

        # 5. VERIFY COMPOUNDED IMPACT FOR AGENTS
        print("\n[STEP 5] Verifying influence on agent context pool...")
        agent_ctx = m.get_compounded_context(active_query={"layer": "backend/persistence"})
        recovered_for_agent = [r for r in agent_ctx if r.get("relevance") == "RECOVERED"]
        
        if not recovered_for_agent:
             raise Exception("FAILED: Recovered item missing in compounded context.")
             
        print(f"Agent Impact Summary: {recovered_for_agent[0].get('impact_summary')}")
        if "[RECALL IMPACT]" not in recovered_for_agent[0].get('impact_summary'):
             raise Exception("FAILED: Agent impact summary formatting error.")

        # 6. REPORT VERIFICATION
        print("\n[STEP 6] Verifying visibility in Report...")
        report = multimodal_report_generator.generate_report(m.mission_id)
        
        timeline_node = next((n for n in report["timeline"] if n.get("retrieval_metadata")), None)
        if not timeline_node:
             raise Exception("FAILED: Retrieval metadata missing from report node.")
             
        print(" - SUCCESS: Impact trace is available for the Creator UI.")

        print("\n--- COGNITIVE EXPLAINABILITY VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_explainability())
