import os
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context

def validate_strategic_dashboard():
    print("--- VALIDANDO OMNIWEB: STRATEGIC BRANCH MERGE DASHBOARD ---")
    
    with set_chip_context("core"):
        from backend.core.database import db_manager
        # 1. Setup multi-branch scenario
        b1 = branch_manager.create_branch(name="Rama Hardened (Ready)")
        b2 = branch_manager.create_branch(name="Rama High Friction (Blocked)")
        b3 = branch_manager.create_branch(name="Rama Divergent (Discard)")
        
        # 2. Simulate B1 towards readiness
        branch_manager.simulate_branch(b1.branch_id)
        # Force approval on B1
        with db_manager.get_connection() as conn:
            verdict = {
                "state": "APPROVED",
                "severity": "nominal",
                "rationale": "Hardened and verified.",
                "persona_details": {"ARCHITECT": {"friction": 0.1, "support": 0.9}}
            }
            conn.execute("UPDATE roadmap_branches SET persona_verdict = ?, merge_readiness = 0.9, branch_state = 'SIMULATED' WHERE branch_id = ?", 
                         (json.dumps(verdict), b1.branch_id))
            conn.commit()

        # 3. Simulate B2 towards blockage
        branch_manager.simulate_branch(b2.branch_id)
        with db_manager.get_connection() as conn:
            verdict = {
                "state": "BLOCKED_BY_PERSONA_TENSION",
                "severity": "high",
                "rationale": "High tension detected.",
                "blocking_roles": ["DESIGNER"],
                "persona_details": {"DESIGNER": {"friction": 0.9, "support": 0.1}}
            }
            conn.execute("UPDATE roadmap_branches SET persona_verdict = ?, constitutional_status = 'VIOLATED' WHERE branch_id = ?", 
                         (json.dumps(verdict), b2.branch_id))
            conn.commit()

        # 4. Simulate B3 towards discard
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE roadmap_branches SET divergence_score = 0.95, merge_readiness = 0.1 WHERE branch_id = ?", (b3.branch_id,))
            conn.commit()

        # 5. GET DASHBOARD
        print("\nGenerando Dashboard Estratégico...")
        dash = branch_manager.get_strategic_dashboard()
        
        print(f"\nDashboard ID: {dash.dashboard_id}")
        print(f"Focus Advice: {dash.focus_recommendation}")
        print(f"Total Branches: {len(dash.active_branches)}")
        
        for s in dash.active_branches:
            print(f"\n[Branch: {s.name}]")
            print(f" - Status: {s.status}")
            print(f" - Readiness: {s.readiness * 100}%")
            print(f" - Friction: {s.friction * 100}%")
            print(f" - Recommendation: {s.recommendation}")
            print(f" - Rationale: {s.rationale}")

        # Final checks
        names = [s.name for s in dash.active_branches]
        assert "Rama Hardened (Ready)" in names
        
        # Cleanup
        branch_manager.delete_branch(b1.branch_id)
        branch_manager.delete_branch(b2.branch_id)
        branch_manager.delete_branch(b3.branch_id)
        print("\n✅ VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_strategic_dashboard()
