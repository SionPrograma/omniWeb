import os
import uuid
import json
from datetime import datetime, timedelta
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_governance_memory():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_MEMORY_INDEX ---")
    
    with set_chip_context("core"):
        # 1. Setup Scenario: Three disparate exceptions with same structural root
        print("Preparando escenario de deuda transversal (CSS/Frontend/Auth)...")
        b1 = branch_manager.create_branch(name="Layout Fix Branch")
        b2 = branch_manager.create_branch(name="Theme Update Branch")
        b3 = branch_manager.create_branch(name="New Auth View Branch")
        
        # Exception 1: Visual drift in Layout
        sid1 = f"ex1-{uuid.uuid4().hex[:4]}"
        # Exception 2: CSS Theme inconsistency
        sid2 = f"ex2-{uuid.uuid4().hex[:4]}"
        # Exception 3: Security Auth drift (Different cluster)
        sid3 = f"ex3-{uuid.uuid4().hex[:4]}"

        with db_manager.get_connection() as conn:
            # Ex 1
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid1, b1.branch_id, "APPROVE_ANYWAY", "Visual layout mismatch.", 0.5, "PENDING", datetime.now(), json.dumps(["Fix CSS selectors"])))
            
            # Ex 2 (Matches Ex 1 via CSS/Visual/Frontend)
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid2, b2.branch_id, "APPROVE_WITH_CONDITIONS", "Theme colors don't match branding.", 0.3, "PENDING", datetime.now(), json.dumps(["Update CSS variables"])))
            
            # Ex 3 (Different: Auth/Security)
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid3, b3.branch_id, "APPROVE_ANYWAY", "Security tokens handling drift.", 0.8, "PENDING", datetime.now(), json.dumps(["Review Auth logic"])))
            
            conn.commit()

        # 2. Extract Report and Clusters
        print("\nGenerando reporte y clusters de memoria...")
        report = branch_manager.get_exceptions_report()
        
        clusters = report.memory_clusters
        print(f"Clusters detectados: {len(clusters)}")
        for c in clusters:
            print(f" - Clúster {c.pattern_id}: {len(c.linked_signal_ids)} señales. Rationale: {c.rationale}")
            print(f"   Dominios: {c.affected_domains}")
            print(f"   Keywords: {c.repeated_keywords}")

        # Assertions
        # There should be at least one cluster containing sid1 and sid2
        css_cluster = next((c for c in clusters if sid1 in c.linked_signal_ids and sid2 in c.linked_signal_ids), None)
        assert css_cluster is not None, "Debería existir un clúster para las excepciones de CSS/Layout."
        assert sid3 not in css_cluster.linked_signal_ids, "La excepción de Auth no debería estar en el clúster de CSS."
        
        # 3. Transversal Recurrence Check
        print("\nVerificando Recurrence Protector con Memoria Indexada...")
        # Even if Ex 2 is new, if it's in a heavy cluster, it might be flagged.
        # Let's see analyze_recurrence for Ex 2
        risk = branch_manager.analyze_recurrence(sid2)
        print(f"Riesgo de Ex 2: {risk.recurrence_state}")
        # If the cluster has 2 signals, risk might be MEDIUM. 
        # Requirement says: "if cluster.structural_risk_level in ['HIGH', 'CRITICAL']"
        # My sig2 currently is MEDIUM because only 2 signals.
        
        print("\nSimulando una tercera señal de CSS para elevar el clúster a HIGH...")
        sid4 = f"ex4-{uuid.uuid4().hex[:4]}"
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid4, b1.branch_id, "PENDING", "Otro problema de CSS.", 0.2, "PENDING", datetime.now(), json.dumps(["Clean CSS"])))
            conn.commit()
            
        report2 = branch_manager.get_exceptions_report()
        clusters = report2.memory_clusters
        css_cluster = next((c for c in clusters if sid1 in c.linked_signal_ids and sid4 in c.linked_signal_ids), None)
        print(f"Nuevo riesgo de clúster: {css_cluster.structural_risk_level}")
        assert css_cluster.structural_risk_level == "HIGH", "El clúster debería escalar a HIGH con 3 señales."
        
        risk4 = branch_manager.analyze_recurrence(sid4)
        print(f"Riesgo de Ex 4 (Gated by Cluster): {risk4.recurrence_state}")
        assert risk4.recurrence_state == "RECURRENT", "Ex 4 debería estar bloqueado por pertenecer a un clúster de alto riesgo."

        # Cleanup
        for b in [b1, b2, b3]: branch_manager.delete_branch(b.branch_id)
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM branch_arbitrations WHERE arbitration_id IN (?, ?, ?, ?)", (sid1, sid2, sid3, sid4))
            conn.commit()
            
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_governance_memory()
