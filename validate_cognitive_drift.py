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

async def validate_cognitive_drift():
    print("--- VALIDATING COGNITIVE DRIFT ANALYSIS ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 0. RESET
        active = mission_manager.get_active_mission()
        if active:
            active.status = MissionStatus.COMPLETED
            mission_manager.save_mission(active)
            mission_manager._active_mission = None

        # 1. SETUP: Misión definida para Backend Auth
        print("\n[STEP 1] Starting Mission: 'Fix Backend Auth Token'...")
        await processor.process("[VISUAL_EVIDENCE] Error de autenticacion", context={})
        m = mission_manager.get_active_mission()
        m.active_goal = "Fix Backend Auth Token validation"
        m.multimodal_history[-1]["hypothesis"] = {
            "layer": "backend/auth",
            "issue_type": "invalid_token",
            "description": "El token no se valida correctamente"
        }
        mission_manager.save_mission(m)

        # 2. DRIFT SCENARIO: El agente empieza a hablar de CSS (UI)
        print("\n[STEP 2] Adding UI snapshots (Layer Shift)...")
        for i in range(2):
            await processor.process(f"[VISUAL_EVIDENCE] El color del fondo es gris {i}", context={})
            m.multimodal_history[-1]["hypothesis"] = {
                "layer": "frontend/ui",
                "issue_type": "color_drift",
                "description": "El estilo del fondo no coincide"
            }
        mission_manager.save_mission(m)
        
        # 3. ANALYZE DRIFT (Layer change should trigger attention)
        print("\n[STEP 3] Analyzing Drift & Trace (Layer Change expected)...")
        report = m.analyze_cognitive_drift()
        print(f"Status: {report['status']} | Score: {report['drift_score']}")
        print(f"Trigger: {report.get('trigger_event', {}).get('role')} at layer {report.get('trigger_event', {}).get('layer')}")
        
        if not report.get('trigger_event'):
             raise Exception("FAILED: No trigger event found in trace.")
        if "trigger" not in report['trigger_event']['role'].lower():
             raise Exception("FAILED: Trigger role incorrect.")

        # 4. DRIFT SCENARIO: Memory Pressure (Manual Reactivation)
        print("\n[STEP 4] Adding manual memory reactivation pressure...")
        node_id = m.multimodal_history[0]["id"]
        m.reactivate_archival_snapshot(node_id, active=True, reason="Force historical context")
        m.reactivate_archival_snapshot(m.multimodal_history[1]["id"], active=True, reason="Second historical context")
        mission_manager.save_mission(m)
        
        # 5. FINAL ANALYZE (Increased score)
        print("\n[STEP 5] Final Drift Audit & Suggestions...")
        final_report = m.analyze_cognitive_drift()
        print(f"Final Status: {final_report['status']} | Final Score: {final_report['drift_score']}")
        print(f"Causal Chain Length: {len(final_report.get('causal_chain', []))}")
        
        # Check Suggestions
        suggestions = final_report.get("suggested_actions", [])
        print(f"Suggestions Found: {len(suggestions)}")
        for s in suggestions:
             print(f" -> [{s['type']}] {s['label']}")
             
        if not any(s['type'] == 'EXCLUDE_NODE' for s in suggestions):
             raise Exception("FAILED: No EXCLUDE_NODE suggestion generated despite memory noise.")
        if not any(s['type'] == 'RESTORE_FOCUS' for s in suggestions):
             raise Exception("FAILED: No RESTORE_FOCUS suggestion despite goal drift.")

        print("\n--- COGNITIVE DRIFT & REALIGNMENT VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_cognitive_drift())
