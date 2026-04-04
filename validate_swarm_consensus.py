import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_swarm_consensus():
    print("--- VALIDATING MISSION STRATEGIC SWARM CONSENSUS (PHASE 76) ---")
    
    with set_chip_context("core"):
        # ----------------------------------------------------
        # 1. SETUP: "Grey Zone" Action (Confidence 0.65)
        # ----------------------------------------------------
        print("[STEP 1] Setting up Grey-Zone Scenario (Conf: 0.65)...")
        from backend.core.database import db_manager
        from datetime import datetime
        with db_manager.get_connection(internal=True) as conn:
             for status in ["ATTENTION_REQUIRED", "DRIFT_WARNING"]:
                  pk = f"ui:{status}::EXCLUDE_NODE"
                  conn.execute("""
                      INSERT OR REPLACE INTO mission_learning (pattern_key, successful_action, total_roi, execution_count, confidence, last_seen)
                      VALUES (?, ?, ?, ?, ?, ?)
                  """, (pk, "EXCLUDE_NODE", 40.0, 1, 0.65, datetime.now().isoformat()))
             conn.commit()
        
        # ----------------------------------------------------
        # 2. TRIGGER: Suggestion Generation
        # ----------------------------------------------------
        print("\n[STEP 2] Generating Suggestions (Should trigger Consensus)...")
        mA = mission_manager.create_mission("Consensus Test Mission")
        mA.multimodal_history.append({"event": "INITIAL", "hypothesis": {"layer": "ui"}})
        # 6 DRIFT events -> DRIFT_WARNING
        for i in range(6): 
             mA.multimodal_history.append({"event": "DRIFT", "hypothesis": {"layer": f"ui/sub_{i}", "id": f"node_{i}", "role": "CONTRIBUTOR"}})
        
        drift = mA.analyze_cognitive_drift()
        print(f"       Current Drift Score: {drift['drift_score']} ({drift['status']})")
        
        suggestions = mA._generate_realignment_suggestions(
            drift["status"], 
            drift["original_focus"], 
            drift["causal_chain"], 
            drift["drift_score"]
        )
        
        match = next((s for s in suggestions if s["type"] == "EXCLUDE_NODE"), None)
        if not match:
             raise Exception("FAILED: Target action not found in suggestions.")
             
        # ----------------------------------------------------
        # 3. VERIFY: Consensus Data
        # ----------------------------------------------------
        print("\n[STEP 3] Verifying Consensus Audit Data...")
        consensus = match.get("consensus")
        if not consensus:
             raise Exception("FAILED: Swarm Consensus was not triggered for grey-zone action.")
             
        print(f"       Consensus Status: {consensus['status']}")
        print(f"       Total Votes: {len(consensus['votes'])}")
        for vote in consensus["votes"]:
             print(f"       - {vote['auditor']}: {vote['vote']} ({vote['reason']})")
             
        print(f"       Confidence Before: {consensus['conf_before']:.2f}")
        print(f"       Confidence After: {consensus['conf_after']:.2f}")
        
        if consensus["conf_after"] == consensus["conf_before"]:
             print("       ⚠️ NOTE: Confidence stayed same (Likely neutral consensus).")
        else:
             print(f"       ✅ SUCCESS: Confidence adjusted by consensus audit.")

        # ----------------------------------------------------
        # 4. NEGATIVE TEST: Obvious Case (Conf: 0.95)
        # ----------------------------------------------------
        print("\n[STEP 4] Verifying 'Obvious' Case Bypass (Conf: 0.95)...")
        with db_manager.get_connection(internal=True) as conn:
             for s_ctx in ["ATTENTION_REQUIRED", "DRIFT_WARNING"]:
                  pk_high = f"ui:{s_ctx}::RESTORE_FOCUS"
                  conn.execute("""
                      INSERT OR REPLACE INTO mission_learning (pattern_key, successful_action, total_roi, execution_count, confidence, last_seen)
                      VALUES (?, ?, ?, ?, ?, ?)
                  """, (pk_high, "RESTORE_FOCUS", 500.0, 10, 0.95, datetime.now().isoformat()))
             conn.commit()
             
        suggestions_v2 = mA._generate_realignment_suggestions(
            drift["status"], drift["original_focus"], drift["causal_chain"], drift["drift_score"]
        )
        match_high = next((s for s in suggestions_v2 if s["type"] == "RESTORE_FOCUS"), None)
        
        if match_high and match_high.get("consensus"):
             raise Exception("FAILED: Consensus triggered for obvious high-confidence action (should bypass).")
        
        print("       ✅ SUCCESS: High-confidence action bypassed consensus (latency saved).")

        print("\n--- SWARM CONSENSUS VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_swarm_consensus())
