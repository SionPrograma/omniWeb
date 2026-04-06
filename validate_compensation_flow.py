import logging
import uuid
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mission(branch_id, title, surface, risk="low", objective="Test objective"):
    handoff_id = str(uuid.uuid4())
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO mission_handoffs (
                    handoff_id, briefing_title, objective, surface_affected, 
                    constraints, risk_level, execution_style, readiness_state, 
                    source_type, gate_data, foreclosure, priority, origin_persona, 
                    supporting_personas, branch_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                handoff_id, title, objective, json.dumps([surface]), json.dumps([]),
                risk, "with_confirmation", "READY", "chat", None, json.dumps({"status": "ACTIVE"}),
                0, "CREATOR_CORE", json.dumps([]), branch_id
            ))
            conn.commit()
    return handoff_id

def validate_compensation_flow():
    print("\n--- VALIDATING OMNIWEB: COMPENSATION PREVIEW & INJECT ---")
    with set_chip_context("core", user_id="1"):
        # Ensure main exists
        if not branch_manager.get_branch("main"):
            branch_manager.create_branch("main", branch_type="main")
        
        # Ensure main is simulated
        branch_manager.simulate_branch("main")
        
        # 1. Create a branch that triggers NEEDS_COMPENSATION (Tester friction)
        branch = branch_manager.create_branch("Exp: Testing Debt", origin="main")
        bid = branch.branch_id
        
        print(f"Rama creada: {bid}")
        
        # Add 6 missions without testing
        for i in range(6):
            create_mission(bid, f"Feature Mission {i}", "ui")
            
        # 2. First Simulation
        print("Ejecutando Simulación Persona-Aware inicial...")
        branch_manager.simulate_branch(bid)
        
        diff = branch_manager.compare_with_main(bid)
        verdict = diff.persona_verdict
        
        print(f"Estado Inicial: {verdict['state']}")
        print(f"Rationale: {verdict['rationale']}")
        
        if not verdict.get('suggested_missions'):
            print("ERROR: No se sugirieron misiones compensatorias.")
            return

        print(f"Compensaciones sugeridas: {len(verdict['suggested_missions'])}")
        for m in verdict['suggested_missions']:
            print(f"- [{m['type']}] sugerido por {m['persona_role']}: {m['objective']}")

        # 3. Inject first compensation
        comp_id = verdict['suggested_missions'][0]['compensation_id']
        print(f"\nInyectando compensación: {comp_id}...")
        
        res = branch_manager.inject_compensation(bid, comp_id)
        print(f"Resultado Inyección: {res['status']}")
        
        # 4. Check Effectiveness Audit
        eff = res.get('effectiveness', {})
        print(f"\n--- AUDITORÍA DE EFECTIVIDAD ---")
        print(f"Estado Resultado: {eff.get('effectiveness_state')}")
        print(f"Impacto: {eff.get('before_state')} -> {eff.get('after_state')}")
        print(f"Rationale: {eff.get('rationale')}")
        print(f"Siguiente Acción: {eff.get('recommended_next_action')}")

        # 5. Check Re-audit result
        # The inject_compensation method calls simulate_branch automatically
        diff_post = branch_manager.compare_with_main(bid)
        verdict_post = diff_post.persona_verdict
        
        print(f"\nEstado Post-Inyección: {verdict_post['state']}")
        print(f"Rationale Post: {verdict_post['rationale']}")
        
        # Check if the mission was actually added
        missions = handoff_manager.get_all(branch_id=bid)
        injected = [m for m in missions if "COMPENSACIÓN" in m.briefing_title]
        print(f"Misiones en rama: {len(missions)} (Inyectadas: {len(injected)})")
        
        # --- NEW: VALIDATE DUPLICATE DETECTION ---
        print("\n--- VALIDANDO DETECCIÓN DE DUPLICADOS ---")
        # Simulating again (happened automatically in inject_compensation)
        diff_dup = branch_manager.compare_with_main(bid)
        verdict_dup = diff_dup.persona_verdict
        
        if verdict_dup.get('suggested_missions'):
            for m in verdict_dup['suggested_missions']:
                if m.get('already_exists'):
                    print(f"✅ DUPLICADO DETECTADO: {m['type']} (Existing ID: {m['existing_mission_id']})")
                else:
                    print(f"⚠️  Sigue recomendando nueva misión: {m['type']} (Fricción persistente)")
        else:
            print("INFO: La compensación fue suficiente para eliminar la recomendación.")

        # --- NEW: VALIDATE REVERT ---
        print("\n--- VALIDANDO REVERTIR COMPENSACIÓN ---")
        mission_id = eff.get('compensation_id') # Wait, eff has audit_id, not compensation_id? 
        # Actually in the code: return {"mission_id": hid, ...}
        mid = res.get('mission_id')
        revert_res = branch_manager.revert_compensation(bid, mid)
        print(f"Resultado Revertir: {revert_res['status']}")
        
        diff_rev = branch_manager.compare_with_main(bid)
        missions_rev = handoff_manager.get_all(branch_id=bid)
        print(f"Misiones en rama tras revertir: {len(missions_rev)}")
        
        # Trace check
        with db_manager.get_connection() as conn:
            trace = conn.execute("SELECT * FROM persona_merge_audits WHERE branch_id = ? ORDER BY created_at DESC", (bid,)).fetchall()
            print(f"Última auditoría: [{trace[0]['state']}] {trace[0]['rationale']}")

        # Cleanup
        branch_manager.delete_branch(bid)

if __name__ == "__main__":
    validate_compensation_flow()
