import sqlite3
import json
import uuid
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.governance_learning_engine import learning_engine

def validate_learning_surface():
    domain = "CoreEngine"
    print(f"\n--- VALIDANDO GOVERNANCE LEARNING SURFACE PARA: {domain} ---")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 1. Inyectar múltiples evidencias (Traces recurrentes)
            print("Inyectando trazas de ineficacia recurrente...")
            for i in range(2):
                conn.execute("""
                    INSERT INTO governance_action_traces (
                        trace_id, target_id, target_type, creator_action, 
                        outcome_status, target_domain, rationale_summary, applied_at
                    ) VALUES (?, ?, 'MISSION', 'REBASE', 'NO_EFFECT', ?, 'Riesgo persiste tras rebase.', ?)
                """, (f"tr-learn-{i}", f"m-learn-{i}", domain, datetime.now().isoformat()))
            
            # 2. Inyectar autopsia confirmatoria
            print("Inyectando autopsia de rama con hallazgo estructural...")
            conn.execute("""
                INSERT INTO governance_branch_autopsies (
                    autopsy_id, branch_id, affected_domains, structural_findings, final_branch_outcome, created_at
                ) VALUES (?, ?, ?, ?, 'DISCARDED', ?)
            """, (str(uuid.uuid4()), "br-failure-1", json.dumps([domain]), json.dumps(["CoreEngine presenta fragilidad estructural circular."]), datetime.now().isoformat()))
            
            conn.commit()
            
            # 3. Disparar el Motor de Aprendizaje
            print("Escaneando evidencias y generando lecciones transversales...")
            learnings = learning_engine.refresh_learning_surface()
            
            if len(learnings) > 0:
                print(f"LECCIONES GENERADAS: {len(learnings)}")
                for i, l in enumerate(learnings):
                    print(f"\n--- LECCIÓN {i+1} [{l.learning_type}] ---")
                    print(f"Summary: {l.lesson_summary}")
                    print(f"Confidence: {l.confidence}")
                    print(f"Behavior: {l.recommended_behavior}")
                    print(f"Evidence count: {l.occurrence_count}")
                
                # 4. Verificar persistencia
                fetch_check = learning_engine.get_learnings()
                if len(fetch_check) >= len(learnings):
                    print("\nConfirmación: Las lecciones han sido consolidadas y persistidas correctamente.")
                else:
                    print(f"\nERROR: Falló la persistencia. Esperados: {len(learnings)}, Encontrados: {len(fetch_check)}")
            else:
                print("ERROR: No se generaron lecciones. Revisar umbrales de evidencia.")

    print("\nDONE: VALIDACIÓN DE GOVERNANCE LEARNING SURFACE COMPLETA.")

if __name__ == "__main__":
    validate_learning_surface()
