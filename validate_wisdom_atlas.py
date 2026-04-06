import sqlite3
import json
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.governance.atlas_schema import apply_atlas_schema
from backend.core.governance.atlas_engine import atlas_engine

def validate_wisdom_atlas_runtime():
    """
    OMNIWEB — BLOQUE: WISDOM ATLAS RUNTIME VALIDATION.
    Ensures that the atlas correctly aggregates diverse wisdom sources.
    """
    print("\nStarting Runtime Validation: Wisdom Atlas UX Layer...")
    
    # 1. Apply Schema
    apply_atlas_schema()

    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 2. Re-create support tables for testing if they don't exist
            # Governance Learnings
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_learning_items (
                learning_item_id TEXT PRIMARY KEY,
                learning_type TEXT,
                target_domain TEXT,
                lesson_summary TEXT,
                recommended_behavior TEXT,
                confidence REAL,
                is_antipattern INTEGER,
                occurrence_count INTEGER,
                created_at TIMESTAMP
            )
            """)
            # Ensure project_id exists
            try:
                conn.execute("ALTER TABLE governance_learning_items ADD COLUMN project_id TEXT DEFAULT 'PROJECT_OMNIWEB_PROD'")
            except sqlite3.OperationalError: pass # Already exists

            
            # Branch Autopsies
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_branch_autopsies (
                autopsy_id TEXT PRIMARY KEY,
                branch_id TEXT NOT NULL,
                branch_goal_summary TEXT,
                affected_domains TEXT,
                final_branch_outcome TEXT,
                structural_findings TEXT,
                confidence REAL,
                created_at TIMESTAMP
            )
            """)

            # Replay Syncs
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_replay_syncs (
                sync_id TEXT PRIMARY KEY,
                simulation_id TEXT,
                target_branch_id TEXT,
                autopsy_id TEXT,
                replay_outcome_state TEXT,
                predicted_effect TEXT,
                actual_outcome_summary TEXT,
                rationale TEXT,
                confidence_delta_proposed REAL
            )
            """)

            # 3. Seed Mock Data for diverse types
            # Node 1: Confinded Learning
            conn.execute("""
                INSERT OR REPLACE INTO governance_learning_items 
                (learning_item_id, learning_type, target_domain, lesson_summary, recommended_behavior, confidence, is_antipattern, occurrence_count, project_id, created_at)
                VALUES ('L-001', 'PATTERN', 'UI_ENGINE', 'Uso de transiciones Bezier para fluidez', 'Aplicar easing 0.4,0,0.2,1', 0.95, 0, 12, 'PROJECT_OMNIWEB_PROD', '2026-04-01')
            """)

            # Node 2: Structural Autopsy
            conn.execute("""
                INSERT OR REPLACE INTO governance_branch_autopsies 
                (autopsy_id, branch_id, branch_goal_summary, affected_domains, final_branch_outcome, structural_findings, confidence, created_at)
                VALUES ('A-101', 'BR-77', 'Refactor del Motor de Inferencia', '["inference", "core"]', 'MERGED', 'El desacoplo de pesos fijos redujo la fricción en un 40%.', 0.88, '2026-04-03')
            """)

            # Node 3: Replay Validation (CONFIRMED)
            conn.execute("""
                INSERT OR REPLACE INTO governance_replay_syncs 
                (sync_id, simulation_id, target_branch_id, autopsy_id, replay_outcome_state, predicted_effect, actual_outcome_summary, rationale, confidence_delta_proposed)
                VALUES ('S-202', 'SIM-99', 'BR-77', 'A-101', 'SIMULATION_CONFIRMED', 'Posible alivio del 30%', 'Alivio real: 40%', 'La predicción del oráculo fue conservadora pero acertada.', 0.05)
            """)

            # Node 4: Experimental / Contradicted
            conn.execute("""
                INSERT OR REPLACE INTO governance_replay_syncs 
                (sync_id, simulation_id, target_branch_id, autopsy_id, replay_outcome_state, predicted_effect, actual_outcome_summary, rationale, confidence_delta_proposed)
                VALUES ('S-203', 'SIM-44', 'BR-01', 'A-02', 'CONTRADICTED_BY_REALITY', 'Éxito crítico', 'Fracaso por dependencia no vista', 'La simulación falló al no trazar la dependencia circular.', -0.1)
            """)

            conn.commit()
            print("Seeded baseline wisdom data for validation.")

    # 4. Trigger Aggregation
    print("Triggering Wisdom Atlas aggregation...")
    atlas_engine.aggregate_all()

    # 5. Verify and Report
    nodes = atlas_engine.get_nodes()
    print(f"\nVALIDATION REPORT — WISDOM ATLAS")
    print(f"Total Nodes Aggregated: {len(nodes)}")
    
    unique_types = set([n.node_type for n in nodes])
    print(f"Unique Node Types Found: {', '.join(unique_types)}")

    for n in nodes[:5]:
        print(f"[{n.node_type}] - {n.title} (Conf: {n.confidence}, Reuse: {n.reusability_score}, Status: {n.status_band})")

    if len(nodes) >= 3 and len(unique_types) >= 3:
        print("\nSUCCESS: All critical wisdom types are correctly mapped to the Atlas.")
    else:
        print("\nWARNING: Some wisdom types are missing or aggregation failed.")

if __name__ == "__main__":
    validate_wisdom_atlas_runtime()
