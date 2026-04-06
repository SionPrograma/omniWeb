import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.governance_audit_trigger_engine import audit_trigger_engine

def validate_root_cause_flow():
    domain = "LegacyCore"
    print(f"\n--- VALIDANDO FORENSIC ROOT CAUSE AUDIT TRIGGER PARA: {domain} ---")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 1. Limpiar rastro previo
            conn.execute("DELETE FROM governance_relief_proposals WHERE source_heatmap_node = ?", (domain,))
            conn.execute("DELETE FROM governance_root_audit_proposals WHERE source_heatmap_node = ?", (domain,))
            
            # 2. Simular 2 misiones de alivio fallidas (Resistencia confirmada)
            for i in range(2):
                p_id = f"relief-fail-{i}"
                conn.execute("""
                    INSERT INTO governance_relief_proposals 
                    (proposal_id, source_heatmap_node, relief_type, status, relief_outcome, baseline_friction_score, created_at)
                    VALUES (?, ?, ?, 'ACCEPTED', 'RESISTANT_HOTSPOT', 90, ?)
                """, (p_id, domain, "TACTICAL_PATCH", (datetime.now() - timedelta(hours=i+1)).isoformat()))
            
            conn.commit()
            print(f"Evidencia inyectada: 2 misiones de alivio fallidas en {domain}.")

            # 3. Disparar el Trigger Engine
            print("Escaneando necesidades de auditoría profunda...")
            proposals = audit_trigger_engine.scan_for_audit_needs()
            
            if len(proposals) > 0:
                p = proposals[0]
                print(f"AUDITORÍA DETECTADA: {p.trigger_state}")
                print(f"Confidence: {p.confidence}")
                print(f"Rationale: {p.rationale}")
                
                # 4. Simular decisión del Creador
                print("Aceptando auditoría de raíz...")
                decision = audit_trigger_engine.process_decision(p.audit_id, "ACCEPT")
                print(f"Acción registrada. Handoff ID: {decision.get('handoff_id')}")
                
                # 5. Verificar duplicidad
                print("Verificando seguridad ante duplicados...")
                dup_proposals = audit_trigger_engine.scan_for_audit_needs()
                if len(dup_proposals) == 0:
                    print("Seguridad confirmada: No se generan duplicados para auditorías activas.")
                else:
                    print("ERROR: Se generó un duplicado.")
            else:
                print("ERROR: No se detectó la necesidad de auditoría.")

    print("\nDONE: VALIDACIÓN DE AUDIT TRIGGER COMPLETA.")

if __name__ == "__main__":
    validate_root_cause_flow()
