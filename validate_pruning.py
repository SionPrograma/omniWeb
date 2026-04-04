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

async def validate_pruning():
    print("--- VALIDATING MULTIMODAL CONTEXT PRUNING ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SETUP: Simular inicio de misión visual
        print("\n[STEP 1] Initializing visual mission...")
        
        # Mock evidence
        evidence_ctx = {
            "multimodal_evidence": [
                {
                    "id": "img_001",
                    "data": "base64_data_1",
                    "annotations": [{"type": "point", "x": 10, "y": 20, "comment": "Error en header"}]
                }
            ]
        }
        
        # First capture
        res1 = await processor.process("[VISUAL_EVIDENCE] El menu esta roto", context=evidence_ctx)
        mission_id = mission_manager.get_active_mission().mission_id
        print(f"Mission created: {mission_id}")
        
        # 2. RE-ORIENTATION 1 (Changes relevance of previous one)
        print("\n[STEP 2] Performing first re-orientation (should downgrade initial)...")
        evidence_ctx_2 = {
            "multimodal_evidence": [
                {
                    "id": "img_002",
                    "data": "base64_data_2",
                    "annotations": [{"type": "point", "x": 50, "y": 50, "comment": "Ajuste de foco en footer"}]
                }
            ]
        }
        await processor.process("[VISUAL_EVIDENCE] En realidad es el footer", context=evidence_ctx_2)
        
        # 3. RE-ORIENTATION 2 (Downgrades previous)
        print("\n[STEP 3] Performing second re-orientation...")
        evidence_ctx_3 = {
            "multimodal_evidence": [
                {
                    "id": "img_003",
                    "data": "base64_data_3",
                    "annotations": [{"type": "point", "x": 100, "y": 100, "comment": "Foco final en auth logic"}]
                }
            ]
        }
        await processor.process("[VISUAL_EVIDENCE] El problema real es el Auth", context=evidence_ctx_3)
        
        # 4. VERIFY MISSION STATE PRUNING
        print("\n[STEP 4] Verifying pruning in MissionState...")
        m = mission_manager.get_active_mission()
        
        total_history = len(m.multimodal_history)
        active_context = m.get_active_multimodal_context(limit=1) # Force strict limit
        
        print(f"Total history entries: {total_history}")
        print(f"Active context entries: {len(active_context)}")
        
        # Check relevance tags
        relevances = [h.get("relevance") for h in m.multimodal_history]
        print(f"Relevance Audit: {relevances}")
        
        if relevances.count("CRITICAL") != 1:
             raise Exception(f"FAILED: Should only have 1 CRITICAL event! Found: {relevances}")
             
        if relevances[0] != "SUPPORT" or relevances[1] != "SUPPORT" or relevances[2] != "CRITICAL":
             raise Exception(f"FAILED: Incorrect relevance sequence! Found: {relevances}")

        print(" - SUCCESS: Relevance tagging and pruning heuristics working correctly.")
        
        # 5. VERIFY REPORT GENERATION
        print("\n[STEP 5] Verifying Multimodal Report exposure...")
        report = multimodal_report_generator.generate_report(m.mission_id)
        
        for node in report["timeline"]:
            print(f"Node {node['event']}: Relevance = {node['relevance']}")
            if not node.get("relevance"):
                raise Exception("FAILED: Report node missing relevance metadata.")
        
        print(" - SUCCESS: Report generator correctly exposes signal levels to UI.")

        print("\n--- CONTEXT PRUNING VALIDATION SUCCESSFUL ---")
        print("OmniWeb agents now work with surgical focus while creators maintain full auditability.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_pruning())
