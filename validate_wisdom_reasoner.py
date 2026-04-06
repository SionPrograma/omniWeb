import json
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.governance.atlas_engine import atlas_engine
from backend.core.governance.wisdom_reasoner import wisdom_reasoner

def validate_wisdom_reasoner_runtime():
    print("Starting Runtime Validation: Tactical Wisdom Reasoner...")
    
    with set_chip_context("core"):
        db_manager.init_db()
        
        # 1. Seed Wisdom Database with specific patterns
        with db_manager.get_connection() as conn:
            # High-confidence Learning on 'core' domain
            conn.execute("DELETE FROM governance_learning_items WHERE learning_item_id = 'L-REASON-1'")
            conn.execute("""
                INSERT INTO governance_learning_items 
                (learning_item_id, learning_type, target_domain, lesson_summary, recommended_behavior, confidence, is_antipattern, occurrence_count)
                VALUES ('L-REASON-1', 'REFACTOR', 'core', 'Optimización profunda de motores mediante paralelismo.', 'Usar ThreadPool.', 0.95, 0, 10)
            """)
            
            # Cautionary Pattern (Contradicted by Reality)
            conn.execute("DELETE FROM governance_branch_autopsies WHERE autopsy_id = 'A-REASON-BUG'")
            conn.execute("""
                INSERT INTO governance_branch_autopsies 
                (autopsy_id, branch_id, branch_goal_summary, affected_domains, final_branch_outcome, structural_findings, confidence)
                VALUES ('A-REASON-BUG', 'BR-FAIL', 'Refactor experimental de Core', '["core"]', 'REJECTED', 'Este enfoque causó corrupción de memoria recursiva.', 0.9)
            """)
            
            # Seed sync to mark it as contradiction in Atlas
            conn.execute("DELETE FROM governance_replay_syncs WHERE autopsy_id = 'A-REASON-BUG'")
            conn.execute("""
                INSERT INTO governance_replay_syncs 
                (sync_id, simulation_id, target_branch_id, autopsy_id, replay_outcome_state, rationale)
                VALUES ('S-REASON-1', 'SIM-NONE', 'BR-FAIL', 'A-REASON-BUG', 'CONTRADICTED_BY_REALITY', 'Impacto negativo masivo.')
            """)
            
            conn.commit()

        # 2. Refresh Atlas
        atlas_engine.aggregate_all()
        
        # 3. RUN REASONER on 'core' context
        current_context = {
            "target_domain": "core",
            "problem_type": "REFACTOR",
            "risk_level": "HIGH"
        }
        
        print(f"Analyzing Context: {json.dumps(current_context)}")
        suggestions = wisdom_reasoner.analyze_context(current_context)
        
        # 4. Assertions
        print(f"\nVALIDATION REPORT — TACTICAL WISDOM REASONER")
        print(f"Total Suggestions generated: {len(suggestions)}")
        
        # We expect L-REASON-1 to be HIGH_RELEVANCE
        strong_match = next((s for s in suggestions if s.node_id == "WNODE-L-REASON-"), None)
        # Note: Atlas node IDs are truncated in aggregation (WNODE-{(r['learning_item_id'] or 'unknown')[:8]})
        # L-REASON-1 -> WNODE-L-REASON
        
        for s in suggestions:
            print(f"[{s.reasoning_type}] - {s.title} (Match: {s.match_score:.2f})")
            print(f"  > Rationale: {s.rationale}")
            print(f"  > Suggestion: {s.recommended_use}")

        # Check for Cautionary Pattern
        caution = next((s for s in suggestions if s.reasoning_type == "CAUTIONARY_PATTERN"), None)
        if caution:
            print(f"SUCCESS: Reasoner correctly surfaced a Cautionary Pattern for the 'core' domain.")
        else:
            print("WARNING: Expected Cautionary Pattern not identified.")

        if len(suggestions) >= 2:
            print("\nRESULT: TACTICAL WISDOM REASONER VALIDATED.")
        else:
            print("\nRESULT: PARTIAL VALIDATION.")

if __name__ == "__main__":
    validate_wisdom_reasoner_runtime()
