import logging
import uuid
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager, ProposedMission
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_main():
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM roadmap_branches WHERE branch_id = 'main'").fetchone()
            if not row:
                conn.execute("""
                    INSERT INTO roadmap_branches (branch_id, name, branch_type, branch_state)
                    VALUES ('main', 'Main Roadmap', 'main', 'ACTIVE')
                """)
                conn.commit()
            branch_manager.simulate_branch("main")

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

def validate_case(name, setup_fn):
    print(f"\n--- VALIDATING CASE: {name} ---")
    with set_chip_context("core", user_id="1"):
        branch = branch_manager.create_branch(f"Case: {name}", origin="main")
        branch_id = branch.branch_id
        
        setup_fn(branch_id)
        
        # Simulate to trigger governance logic
        branch_manager.simulate_branch(branch_id)
        
        # Get diff and verdict
        diff = branch_manager.compare_with_main(branch_id)
        verdict = diff.persona_verdict
        
        print(f"Merge State: {verdict['state'] if verdict else 'NONE'}")
        print(f"Rationale: {verdict['rationale'] if verdict else 'NONE'}")
        if verdict and verdict.get('required_compensations'):
            print(f"Compensations: {verdict['required_compensations']}")
            
        # Try to merge
        res = branch_manager.merge_branch(branch_id)
        print(f"Merge Attempt Status: {res.get('status')}")
        if res.get('reason'):
            print(f"Block Reason: {res.get('reason')}")
            
        # Cleanup
        branch_manager.delete_branch(branch_id)

def setup_approved(bid):
    create_mission(bid, "UI Polishing", "ui")
    create_mission(bid, "Docs update", "docs")

def setup_bias_warning(bid):
    # Only UI, no Core/Support
    for i in range(5):
        create_mission(bid, f"UI Pixel {i}", "ui")

def setup_needs_compensation(bid):
    # Many Core, 0 Tests
    for i in range(3):
        create_mission(bid, f"Core Logic {i}", "core", risk="high")

def setup_blocked(bid):
    # Force Auditor veto via high accumulated risk (or manual constitution violation)
    # The auditor vetoes if len(high_risk) > 0 and constitutional_status == "VIOLATED"
    # Actually, current heuristic: friction > 1.2 markers violated.
    for i in range(10):
        create_mission(bid, f"Extreme Risk {i}", "core", risk="high")

if __name__ == "__main__":
    ensure_main()
    validate_case("APPROVED", setup_approved)
    validate_case("ROLE_BIAS_WARNING", setup_bias_warning)
    validate_case("NEEDS_COMPENSATION", setup_needs_compensation)
    validate_case("BLOCKED_BY_TENSIÓN", setup_blocked)
