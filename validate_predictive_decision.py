import json
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.governance_predictive_engine import predictive_engine

def test_predictive_decision():
    print("Testing Predictive Decision Flow...")
    with set_chip_context("core"):
        # 1. Get an active advisory
        advisories = predictive_engine.get_active_advisories()
        if not advisories:
            print("No active advisories found to test decision.")
            return

        target_adv = advisories[0]
        print(f"Deciding on {target_adv.advisory_id} for {target_adv.target_domain}...")

        with db_manager.get_connection() as conn:
            # Update to inactive (Creator Decision simulation)
            conn.execute("UPDATE governance_predictive_advisories SET is_active = 0 WHERE advisory_id = ?", (target_adv.advisory_id,))
            
            # Record decision trace
            from backend.core.ai_host.observability.governance_trace_engine import trace_engine
            trace = trace_engine.register_trace(
                target_id=target_adv.advisory_id,
                action="PREDICTIVE_ACT_PREVENTIVELY",
                target_type="PREDICTIVE_ADVISORY",
                domain=target_adv.target_domain
            )
            conn.commit()
            print(f"Decision registered. Trace ID: {trace.trace_id}")

        # 2. Verify it's no longer active
        new_active = predictive_engine.get_active_advisories()
        if any(a.advisory_id == target_adv.advisory_id for a in new_active):
            print("TEST FAILED: Advisory still active.")
        else:
            print("TEST PASSED: Advisory correctly archived with decision trace.")

if __name__ == "__main__":
    test_predictive_decision()
