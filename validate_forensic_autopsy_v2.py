import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.governance_autopsy_engine import autopsy_engine

def validate_forensic_autopsy():
    branch_id = "br_test_autopsy"
    print(f"\n--- VALIDANDO FORENSIC BRANCH AUTOPSY PARA: {branch_id} ---")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 0. Asegurar tabla
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_branch_autopsies (
                autopsy_id TEXT PRIMARY KEY,
                branch_id TEXT NOT NULL,
                branch_goal_summary TEXT,
                affected_domains TEXT,
                hotspot_history TEXT,
                advisories_generated TEXT,
                creator_actions_summary TEXT,
                debt_events TEXT,
                resistance_events TEXT,
                root_audit_events TEXT,
                final_branch_outcome TEXT,
                lessons_learned TEXT,
                structural_findings TEXT,
                recommended_followup TEXT,
                confidence REAL,
                created_at TIMESTAMP
            )
            """)
            
            # 1. Limpieza
            conn.execute("DELETE FROM roadmap_branches WHERE branch_id = ?", (branch_id,))
            conn.execute("DELETE FROM mission_handoffs WHERE branch_id = ?", (branch_id,))
            conn.execute("DELETE FROM governance_branch_autopsies WHERE branch_id = ?", (branch_id,))
            
            # 2. Mocking Branch & Missions
            conn.execute("""
                INSERT INTO roadmap_branches (branch_id, name, branch_type, branch_state)
                VALUES (?, ?, 'tactical', 'ACTIVE')
            """, (branch_id, "Experimento: Refactor Core Legacy"))
            
            h_id = f"h_aut_{uuid.uuid4().hex[:6]}"
            conn.execute("""
                INSERT INTO mission_handoffs (handoff_id, briefing_title, objective, surface_affected, branch_id)
                VALUES (?, ?, ?, ?, ?)
            """, (h_id, "Refactor Core", "Cleanup de dependencias circulares", json.dumps(["CoreEngine"]), branch_id))
            
            # 3. Inyectar Intento de Alivio FALLIDO (Resistencia)
            p_id = f"p_rel_{uuid.uuid4().hex[:6]}"
            conn.execute("""
                INSERT INTO governance_relief_proposals 
                (proposal_id, source_heatmap_node, relief_type, status, relief_outcome, associated_handoff_id, baseline_friction_score, created_at)
                VALUES (?, 'CoreEngine', 'TACTICAL_PATCH', 'ACCEPTED', 'RESISTANT_HOTSPOT', ?, 85.0, ?)
            """, (p_id, h_id, datetime.now().isoformat()))
            
            conn.commit()
            print(f"Evidencia inyectada en {branch_id}: 1 misión y 1 alivio resistente.")

            # 4. Trigger Autopsy (Simulating branch closure)
            print("Generando autopsia forense...")
            autopsy = autopsy_engine.generate_autopsy(branch_id, "MERGED")
            
            if autopsy:
                print(f"AUTOPSIA GENERADA: {autopsy.autopsy_id}")
                print(f"Outcome: {autopsy.final_branch_outcome}")
                print(f"Lección Aprendida: {autopsy.lessons_learned[0] if autopsy.lessons_learned else 'None'}")
                print(f"Hallazgo Estructural: {autopsy.structural_findings[0] if autopsy.structural_findings else 'None'}")
                
                # 5. Verificación de Persistencia
                all_autopsies = autopsy_engine.get_autopsies(branch_id=branch_id)
                if len(all_autopsies) > 0:
                    print("Verificación de base de datos exitosa.")
                else:
                    print(f"ERROR: Autopsia no encontrada en base de datos. IDs en DB: {len(autopsy_engine.get_autopsies())}")
            else:
                print("ERROR: Falló la generación de autopsia.")

    print("\nDONE: VALIDACIÓN DE FORENSIC BRANCH AUTOPSY COMPLETA.")

if __name__ == "__main__":
    validate_forensic_autopsy()
