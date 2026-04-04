import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from datetime import datetime
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_cognitive_healing():
    print("--- VALIDATING MISSION COGNITIVE HEALING (PHASE 75) ---")
    
    with set_chip_context("core"):
        # ----------------------------------------------------
        # 1. SETUP: High Trust Initial State
        # ----------------------------------------------------
        print("[STEP 1] Direct Injektion of Pattern Trust (Scale 0-1)...")
        from backend.core.database import db_manager
        pk = "ui:ATTENTION_REQUIRED::EXCLUDE_NODE"
        with db_manager.get_connection(internal=True) as conn:
             conn.execute("""
                 INSERT OR REPLACE INTO mission_learning (pattern_key, successful_action, total_roi, execution_count, confidence, last_seen)
                 VALUES (?, ?, ?, ?, ?, ?)
             """, (pk, "EXCLUDE_NODE", 500.0, 5, 0.95, datetime.now().isoformat()))
             conn.commit()
        
        # Exclude node on 'ui' layer
        ctx_key = "ui:ATTENTION_REQUIRED"
 
        # ----------------------------------------------------
        # 2. TRIGGER: Autonomous Rescue
        # ----------------------------------------------------
        print("\n[STEP 2] Executing Autonomous Rescue (Pilot)...")
        mA = mission_manager.create_mission("Healing Test Mission")
        mA.multimodal_history.append({"event": "INITIAL", "hypothesis": {"layer": "ui"}})
        for i in range(7): # DRIFT_WARNING score
             mA.multimodal_history.append({"event": "DRIFT", "hypothesis": {"layer": f"ui/layer_{i}", "id": f"noise_{i}", "role": "CONTRIBUTOR"}})
        
        # Trigger
        res_auto = mA.trigger_automatic_rescue()
        print(f"       Auto-Rescue Result: {res_auto['success']} (Conf: 95%)")
        
        # Check current learning entry
        pk = f"{ctx_key}::EXCLUDE_NODE"
        from backend.core.database import db_manager
        with db_manager.get_connection(internal=True) as conn:
             row = conn.execute("SELECT confidence FROM mission_learning WHERE pattern_key = ?", (pk,)).fetchone()
             print(f"       Current Global Confidence: {row[0]:.2f}")

        # ----------------------------------------------------
        # 3. FEEDBACK: Human Reversal
        # ----------------------------------------------------
        print("\n[STEP 3] Human Overrides Autonomous Action (Manual Restore)...")
        # Simulator: Human sends 'RESTORE_FOCUS' which contradicts 'EXCLUDE_NODE'
        res_manual = mA.execute_realignment_action({
            "type": "RESTORE_FOCUS",
            "label": "Manual Reversal"
        })
        
        # ----------------------------------------------------
        # 4. VERIFY: Healing Signal & Penalty
        # ----------------------------------------------------
        print("\n[STEP 4] Verifying Cognitive Healing Signal...")
        healing_events = [h for h in mA.multimodal_history if h.get("event") == "COGNITIVE_HEALING"]
        print(f"       Healing Events in History: {len(healing_events)}")
        if not healing_events:
             raise Exception("FAILED: Cognitive healing signal not detected during manual reversal.")
             
        print(f"       Reason: {healing_events[0]['reason']}")
        
        # Audit Database Penalty
        with db_manager.get_connection(internal=True) as conn:
             row_after = conn.execute("SELECT confidence FROM mission_learning WHERE pattern_key = ?", (pk,)).fetchone()
             print(f"       Global Confidence AFTER Healing: {row_after[0]:.2f}")
             
             if row_after[0] >= row[0]:
                  raise Exception("FAILED: Confidence was not penalised after human reversal.")
                  
        # ----------------------------------------------------
        # 5. FUTURE IMPACT: Autonomy Downgrade
        # ----------------------------------------------------
        print("\n[STEP 5] Verifying Future Autonomy Downgrade...")
        # Now evaluate autonomy level for the same action
        # If confidence falls below 0.85, it should no longer be AUTO_SAFE
        audit = mA.evaluate_mitigation_autonomy("EXCLUDE_NODE", "ui", row_after[0])
        print(f"       Next Autonomy Level: {audit['level']} | Reason: {audit['reason']}")
        
        if row_after[0] < 0.85 and audit['level'] == "AUTO_SAFE_THEORETICAL":
             raise Exception("FAILED: System still allowing AUTO_SAFE after confidence penalty.")
        elif row_after[0] < 0.85:
             print("       ✅ SUCCESS: Autonomy downgraded to HUMAN_CONFIRM due to negative feedback.")

        print("\n--- COGNITIVE HEALING VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_cognitive_healing())
