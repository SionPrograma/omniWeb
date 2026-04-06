import json
from datetime import datetime, timedelta
import uuid

# Mock proposal created 1 hour ago
handoff_id = "test-handoff-001"
created_ts = (datetime.now() - timedelta(hours=1)).isoformat()
affected_surface = ["backend/core/config.py"]

# Mocking the Engine logic
def mock_check_rebase(creation_time, surfaces, history_events, current_locks):
    rebase_report = {"status": "STILL_VALID", "detected_changes": [], "conflicts": []}
    
    # 1. Surface Mutations
    for event in history_events:
        if event['module'] in surfaces and event['ts'] > creation_time:
            rebase_report["detected_changes"].append({"detail": f"Mutation on {event['module']}", "ts": event['ts']})
            rebase_report["status"] = "NEEDS_REFRESH"
            
    # 2. Conflicts
    for lock in current_locks:
        if lock in surfaces:
            rebase_report["conflicts"].append(f"Lock on {lock}")
            rebase_report["status"] = "CONFLICTED"
            
    return rebase_report

# Case A: Nominal (No events)
r1 = mock_check_rebase(created_ts, affected_surface, [], [])
print(f"Case A: {r1['status']}")

# Case B: Surface touched since then
events = [{'module': 'backend/core/config.py', 'ts': (datetime.now() - timedelta(minutes=10)).isoformat()}]
r2 = mock_check_rebase(created_ts, affected_surface, events, [])
print(f"Case B: {r2['status']} - Changes: {len(r2['detected_changes'])}")

# Case C: Conflicted by active lock
locks = ["backend/core/config.py"]
r3 = mock_check_rebase(created_ts, affected_surface, events, locks)
print(f"Case C: {r3['status']} - Conflicts: {len(r3['conflicts'])}")
