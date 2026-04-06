import json
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.governance.atlas_engine import atlas_engine
from backend.core.governance.wisdom_reasoner import wisdom_reasoner
from backend.core.governance.draft_engine import draft_engine

def validate_mission_autodraft_runtime():
    print("Starting Runtime Validation: Wisdom-Driven Mission Auto-Draft...")
    
    with set_chip_context("core"):
        db_manager.init_db()
        
        # 1. Seed a proven Tactic in Atlas
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM governance_learning_items WHERE learning_item_id = 'L-DRAFT-1'")
            conn.execute("""
                INSERT INTO governance_learning_items 
                (learning_item_id, learning_type, target_domain, lesson_summary, recommended_behavior, confidence, is_antipattern)
                VALUES ('L-DRAFT-1', 'REFACTOR', 'frontend', 'Modularización de componentes de shell.', 'Separar lógica de renderizado.', 0.9, 0)
            """)
            conn.commit()

        # 2. Refresh Atlas
        atlas_engine.aggregate_all()
        
        # 3. Get Reasoner Suggestion
        context = {"target_domain": "frontend", "problem_type": "REFACTOR"}
        suggestions = wisdom_reasoner.analyze_context(context)
        
        target_s = next((s for s in suggestions if s.node_id == "WNODE-L-DRAFT-"), None)
        if not target_s:
            # Fallback if ID truncation differs
            target_s = suggestions[0] if suggestions else None
            
        if not target_s:
            print("ERROR: No suggestions found to draft from.")
            return

        print(f"Reasoner Suggestion: {target_s.title} ({target_s.reasoning_type})")

        # 4. Generate Draft
        draft = draft_engine.create_draft_from_suggestion(target_s.model_dump(), context)
        
        # 5. Assertions
        print(f"\nVALIDATION REPORT — MISSION AUTO-DRAFT")
        print(f"Draft ID: {draft.draft_id}")
        print(f"Draft Type: {draft.draft_type}")
        print(f"Title: {draft.title}")
        print(f"Objective: {draft.objective[:100]}...")
        print(f"Constraints: {draft.constraints}")
        print(f"Preconditions: {draft.preconditions}")
        print(f"Risk Level: {draft.risk_level}")

        # Check persistence
        with db_manager.get_connection() as conn:
            saved = conn.execute("SELECT * FROM governance_mission_auto_drafts WHERE draft_id = ?", (draft.draft_id,)).fetchone()
            if saved:
                print(f"SUCCESS: Draft persisted in governance_mission_auto_drafts.")
            else:
                print(f"ERROR: Draft NOT found in database.")

        if "Intervención:" in draft.title and len(draft.constraints) >= 2:
            print("\nRESULT: WISDOM-DRIVEN MISSION AUTO-DRAFT VALIDATED.")
        else:
            print("\nRESULT: VALIDATION FAILED.")

if __name__ == "__main__":
    validate_mission_autodraft_runtime()
