import sqlite3
import json
import uuid
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.governance.atlas_engine import atlas_engine
from backend.core.governance.graph_engine import graph_engine

def validate_wisdom_graph_runtime():
    print("Starting Runtime Validation: Wisdom Graph Explorer...")
    
    with set_chip_context("core"):
        db_manager.init_db()
        with db_manager.get_connection() as conn:
            # 1. Seed Linked Data
            # Autopsy A-999
            conn.execute("DELETE FROM governance_branch_autopsies WHERE autopsy_id = 'A-999'")
            conn.execute("""
                INSERT INTO governance_branch_autopsies 
                (autopsy_id, branch_id, branch_goal_summary, affected_domains, final_branch_outcome, structural_findings, confidence)
                VALUES ('A-999', 'BR-GRAPH-TEST', 'Prueba de Grafo Estructural', '["core", "ui"]', 'MERGED', 'Hallazgo base para el grafo.', 0.95)
            """)
            
            # Replay Sync S-999 (Linking to A-999)
            conn.execute("DELETE FROM governance_replay_syncs WHERE sync_id = 'S-999'")
            conn.execute("""
                INSERT INTO governance_replay_syncs 
                (sync_id, simulation_id, target_branch_id, autopsy_id, replay_outcome_state, predicted_effect, actual_outcome_summary, rationale)
                VALUES ('S-999', 'SIM-G1', 'BR-GRAPH-TEST', 'A-999', 'SIMULATION_CONFIRMED', 'Efecto X', 'Resultado X', 'Validación exitosa del vínculo.')
            """)

            # Learning L-999 (Related Domain)
            conn.execute("DELETE FROM governance_learning_items WHERE learning_item_id = 'L-999'")
            conn.execute("""
                INSERT INTO governance_learning_items 
                (learning_item_id, learning_type, target_domain, lesson_summary, recommended_behavior, confidence, is_antipattern, occurrence_count)
                VALUES ('L-999', 'PATRON', 'core', 'Lección central vinculada.', 'Seguir patrón.', 0.9, 0, 5)
            """)

            # Decision D-999 (Triggered by Autopsy A-999 via Branch)
            conn.execute("DELETE FROM governance_decision_ledger WHERE ledger_id = 'D-999'")
            conn.execute("""
                INSERT INTO governance_decision_ledger 
                (ledger_id, decision_type, target_ref_type, target_id, actor, action_taken, rationale, severity_context, active_flag)
                VALUES ('D-999', 'STRATEGIC_PIVOT', 'BRANCH', 'BR-GRAPH-TEST', 'CREATOR', 'EXECUTED', 'Pivote estratégico basado en hallazgos estructurales.', 'MODERATE', 1)
            """)

            # Learning L-888 (Sharing domain with L-999 to test cluster)
            conn.execute("DELETE FROM governance_learning_items WHERE learning_item_id = 'L-888'")
            conn.execute("""
                INSERT INTO governance_learning_items 
                (learning_item_id, learning_type, target_domain, lesson_summary, recommended_behavior, confidence, is_antipattern, occurrence_count)
                VALUES ('L-888', 'TACTIC', 'core', 'Otra lección de core.', 'Optimizar.', 0.85, 0, 2)
            """)
            
            conn.commit()

        # 2. Trigger Atlas Refresh
        print("Refreshing Wisdom Atlas...")
        atlas_engine.aggregate_all()
        
        # 3. Trigger Graph Refresh
        print("Refreshing Wisdom Graph...")
        graph_engine.rebuild_graph()
        
        # 4. Assertions
        graph_data = graph_engine.get_graph_data()
        nodes = graph_data["nodes"]
        links = graph_data["links"]
        
        print(f"\nVALIDATION REPORT — WISDOM GRAPH")
        print(f"Total Nodes in Graph: {len(nodes)}")
        print(f"Total Links in Graph: {len(links)}")
        
        # Check for specific link (Sync -> Autopsy)
        sync_link = next((l for l in links if l["type"] == "CONFIRMED_BY"), None)
        if sync_link:
            print(f"SUCCESS: Found link 'CONFIRMED_BY' from {sync_link['source']} to {sync_link['target']}")
        else:
            print("WARNING: Expected 'CONFIRMED_BY' link not found.")
            
        # Check for node diversity
        node_types = set(n["type"] for n in nodes)
        print(f"Node Types identified: {', '.join(node_types)}")
        
        if len(links) > 0 and len(node_types) >= 3:
            print("\nRESULT: RATIONAL WISDOM GRAPH VALIDATED.")
        else:
            print("\nRESULT: PARTIAL VALIDATION. Check linking rules.")

if __name__ == "__main__":
    validate_wisdom_graph_runtime()
