import os
import json
import uuid
from datetime import datetime, timedelta
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.governance_heatmap_engine import heatmap_engine
from backend.core.ai_host.observability.governance_relief_engine import relief_engine
from backend.core.ai_host.observability.governance_resistance_engine import resistance_engine

def validate_structural_resistance():
    print("--- VALIDANDO OMNIWEB: STRUCTURAL RESISTANCE DETECTOR ---")
    
    with set_chip_context("core"):
        # 1. Setup a Hotspot
        domain = "CoreEngine.Logic"
        print(f"Creando hotspot artificial en {domain}...")
        
        with db_manager.get_connection() as conn:
            # Inject debt and advisories to make it HOT
            conn.execute("DELETE FROM governance_risk_overrides WHERE affected_domain = ?", (domain,))
            conn.execute("DELETE FROM governance_rebase_recommendations WHERE affected_domain = ?", (domain,))
            conn.execute("DELETE FROM governance_relief_proposals WHERE source_heatmap_node = ?", (domain,))
            
            for i in range(5):
                conn.execute(
                    "INSERT INTO governance_risk_overrides (override_id, target_id, override_type, affected_domain, is_active, debt_state) VALUES (?, 'dummy_task', 'TECHNICAL', ?, 1, 'ACTIVE')",
                    (str(uuid.uuid4()), domain)
                )
            for i in range(3):
                conn.execute(
                    "INSERT INTO governance_rebase_recommendations (recommendation_id, affected_domain, recommendation_state) VALUES (?, ?, 'PENDING')",
                    (str(uuid.uuid4()), domain)
                )
            conn.commit()
            
        nodes = heatmap_engine.get_friction_heatmap()
        target = next((n for n in nodes if n.domain == domain), None)
        print(f"Heatmap: {target.domain} - Score: {target.friction_score} - Band: {target.severity_band}")
        assert target.friction_score >= 50
        
        # 2. Generate and Accept Relief Mission
        print("\nGenerando propuesta de alivio...")
        proposals = relief_engine.generate_proposals()
        p = next((prop for prop in proposals if prop.source_heatmap_node == domain), None)
        assert p is not None
        print(f"Propuesta generada: {p.proposal_id} - Type: {p.relief_type}")
        
        print("\nAceptando misión de alivio (Baseline capture)...")
        res = relief_engine.process_decision(p.proposal_id, 'ACCEPT')
        assert res["status"] == "success"
        
        # Verify baseline
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT baseline_friction_score, relief_outcome FROM governance_relief_proposals WHERE proposal_id = ?", (p.proposal_id,)).fetchone()
            print(f"Baseline capturado: {row['baseline_friction_score']} pts. Outcome: {row['relief_outcome']}")
            assert row['baseline_friction_score'] == target.friction_score
            assert row['relief_outcome'] == 'UNDER_OBSERVATION' # It starts with this before evaluation
            
        # 3. Simulate Evaluation: RELIEF_PENDING (Too soon)
        print("\nEvaluando alivio (T+0):")
        evals = resistance_engine.evaluate_all_active_reliefs()
        ev = next((e for e in evals if e.proposal_id == p.proposal_id), None)
        # Note: If evaluate_all_active_reliefs returns None because of time guard, it's correct
        if ev:
            print(f"Outcome: {ev.outcome} - Rationale: {ev.rationale}")
        else:
            print("Evaluación omitida por ventana de tiempo (PENDING correcto)")

        # 4. Simulate EFFECTIVE_RELIEF
        print("\nSimulando enfriamiento (Effective Relief)...")
        with db_manager.get_connection() as conn:
            # Delete ALL debt and advisories for this domain to force a drop
            conn.execute("DELETE FROM governance_risk_overrides WHERE affected_domain = ?", (domain,))
            conn.execute("DELETE FROM governance_rebase_recommendations WHERE affected_domain = ?", (domain,))
            # Force older timestamp to skip time guard
            old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
            conn.execute("UPDATE governance_relief_proposals SET updated_at = ? WHERE proposal_id = ?", (old_time, p.proposal_id))
            conn.commit()
            
        evals = resistance_engine.evaluate_all_active_reliefs()
        ev = next((e for e in evals if e.proposal_id == p.proposal_id), None)
        assert ev is not None
        print(f"Resultado: {ev.outcome} (Delta: {ev.delta_score})")
        assert ev.outcome == "EFFECTIVE_RELIEF"

        # 5. Verify Heatmap integration
        print("\nVerificando Heatmap con alivio activo...")
        nodes = heatmap_engine.get_friction_heatmap()
        target = next((n for n in nodes if n.domain == domain), None)
        print(f"Heatmap signals: relief_outcome={target.signals['relief_outcome']}, current={target.signals['relief_current']}")
        assert target.signals['relief_status'] == "ACTIVE"

        # 6. Simulate RESISTANT_HOTSPOT
        print("\nSimulando resistencia estructural (Resistant Hotspot)...")
        with db_manager.get_connection() as conn:
            for i in range(10):
                conn.execute(
                    "INSERT INTO governance_risk_overrides (override_id, target_id, override_type, affected_domain, is_active, debt_state) VALUES (?, 'dummy_task', 'TECHNICAL', ?, 1, 'ACTIVE')",
                    (str(uuid.uuid4()), domain)
                )
            old_time = (datetime.now() - timedelta(hours=4)).isoformat()
            conn.execute("UPDATE governance_relief_proposals SET updated_at = ?, observers_count = 5 WHERE proposal_id = ?", (old_time, p.proposal_id))
            conn.commit()
            
        evals = resistance_engine.evaluate_all_active_reliefs()
        ev = next((e for e in evals if e.proposal_id == p.proposal_id), None)
        print(f"Resultado: {ev.outcome} (Current: {ev.current_score})")
        print(f"Rationale: {ev.rationale}")
        assert ev.outcome == "RESISTANT_HOTSPOT"
        
        # 7. Check Heatmap Band
        nodes = heatmap_engine.get_friction_heatmap()
        target = next((n for n in nodes if n.domain == domain), None)
        print(f"Banda final Heatmap: {target.severity_band}")
        assert target.severity_band == "RESISTANT"

        print("\nDONE: VALIDACIÓN DE RESISTENCIA ESTRUCTURAL COMPLETADA.")

if __name__ == "__main__":
    validate_structural_resistance()
