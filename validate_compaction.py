import sys
import os
import json
from datetime import datetime

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus

def validate_context_compactor():
    print("--- VALIDATING MISSION CONTEXT COMPACTOR ---")
    
    with set_chip_context("core"):
        # 1. Apply Migrations
        print("Applying migrations...")
        db_manager.run_migrations()
        
        # 2. Cleanup previous
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM system_missions WHERE active_goal LIKE 'TEST_COMPACT_%'")
            conn.commit()

        # 3. Create Complex Mission
        print("\nCreating complex mission scenario...")
        goal = "TEST_COMPACT_MISSION: Refactor de API con restricciones de seguridad y guia multimodal activa"
        m = mission_manager.create_mission(goal)
        
        # Set constraints
        m.parameters["forbidden_paths"] = ["/etc/shadow", "/root"]
        m.parameters["frozen_layers"] = ["kernel_v1", "auth_legacy"]
        m.parameters["conservative_mode"] = True
        
        # Set governance data
        m.context_snap["governance_health"] = {"score": 0.85, "incidents": 1}
        m.blocked_reasons.append("Intento de acceso a zona congelada (kernel_v1)")
        
        # Set multimodal context
        m.visual_context = {
            "hypothesis": {
                "remediation_summary": "Actualizar headers de seguridad en el middleware global"
            }
        }
        
        # 4. Save (Triggers Compaction)
        print("Saving mission to trigger auto-compaction...")
        mission_manager.save_mission(m)
        
        # 5. Reload and Verify
        print("\nVerifying compact digest...")
        reloaded = mission_manager.get_mission_by_id(m.mission_id)
        
        digest = reloaded.compact_digest
        if not digest:
            raise Exception("Compact digest was not generated!")
            
        print(f"DIGEST GENERATED:")
        print(f" - Goal Compact: {digest.goal_compact}")
        print(f" - Status: {digest.status_label}")
        print(f" - Readiness: {digest.readiness}")
        print(f" - Gov Score: {digest.governance_score}")
        print(f" - Constraints: {digest.active_constraints}")
        print(f" - Multimodal: {digest.multimodal_summary}")
        print(f" - Next Step: {digest.next_step_hint}")
        
        # Assertions
        assert "Refactor de API" in digest.goal_compact
        assert len(digest.active_constraints) >= 3
        assert digest.governance_score == 0.9 # BAJO GUARDIA status
        assert "Actualizar headers" in digest.multimodal_summary
        
        print("\n--- VALIDATION SUCCESSFUL ---")
        print("OmniWeb now carries high-density, low-noise context for every mission.")

if __name__ == "__main__":
    try:
        validate_context_compactor()
    except Exception as e:
        print(f"\n--- VALIDATION FAILED: {e} ---")
        import traceback
        traceback.print_exc()
