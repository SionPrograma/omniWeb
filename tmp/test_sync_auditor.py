import asyncio
import sys
import json
from datetime import datetime

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.ai_host.memory.sync_auditor import sync_auditor
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
import backend.core.permissions

def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

async def test_sync_auditor():
    print("\n--- CROSS-DOMAIN SYNC AUDITOR TEST ---")
    
    with set_chip_context("core"):
        # 1. SETUP EVIDENCE
        print("Setup: Injecting cross-domain evidence...")
        
        # A. Semantic Dependency: Mission in 'auth' referencing 'ui'
        handoff_manager.add_proposal({
            "objective": "Implementar JWT hardening en el backend. Nota: requiere actualizacion en el dominio ui para manejar nuevos headers.",
            "surface_affected": ["auth"],
            "risk_level": "medium"
        })

        # B. Temporal Impact: Push in 'core' and blocked mission in 'db_engine'
        handoff_manager.add_proposal({
            "objective": "Migracion de esquemas DB.",
            "surface_affected": ["db_engine"],
            "readiness_state": "BLOCKED"
        })
        
        with db_manager.get_connection() as conn:
            # Simulate a successful push in 'core' 1 hour ago
            conn.execute("""
                INSERT INTO atomic_push_sessions (push_id, roadmap_group_id, state, updated_at, current_step_index, execution_plan, step_statuses) 
                VALUES (?, ?, ?, datetime('now', '-1 hour'), 0, '[]', '{}')
            """, ("test-push-a", "surface_core", "COMPLETED"))
            conn.commit()

        # 2. AUDIT
        print("\nAuditing cross-domain relations...")
        rels = sync_auditor.audit_cross_domain_sync()
        for r in rels:
            print(f"Detected: {r.relation_type} between {r.domain_a} and {r.domain_b} (Sev: {r.severity})")
            print(f"  Rationale: {r.evidence_summary}")

        assert len(rels) >= 2
        print("Dependency detection: PASSED")

        # 3. SUGGEST COORDINATION
        contract_rel = next(r for r in rels if r.relation_type == "CONTRACT_DEPENDENCY")
        print(f"\nSuggesting coordination mission for relation {contract_rel.relation_id[:6]}...")
        suggestion = sync_auditor.get_coordination_mission_suggestion(contract_rel.relation_id)
        
        assert suggestion is not None
        assert "Sincronizar contrato" in suggestion["objective"]
        print(f"Success: Coordination suggested: {suggestion['objective'][:50]}...")
        print("Coordination bridge: PASSED")

        print("\nAll sync auditor validations SUCCESSFUL.")

        # Cleanup
        # (Custom cleanup for handoffs and forensics)
        with db_manager.get_connection() as conn:
             conn.execute("DELETE FROM mission_handoffs WHERE objective LIKE '%JWT%' OR objective LIKE '%Migracion%'")
             conn.execute("DELETE FROM atomic_push_sessions WHERE push_id = 'test-push-a'")
             conn.commit()

if __name__ == "__main__":
    asyncio.run(test_sync_auditor())
