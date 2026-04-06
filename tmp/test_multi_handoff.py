import re
from typing import Dict, Any

# Mock HandoffManager
class MockHandoff:
    def __init__(self, id, obj):
        self.handoff_id = id
        self.objective = obj
        self.readiness_state = "PENDING"
    def model_dump(self): return {"handoff_id": self.handoff_id, "objective": self.objective, "readiness_state": self.readiness_state}

class MockHandoffManager:
    def __init__(self): self.h = {}
    def add_proposal(self, m, g, source):
        hid = str(len(self.h)+1)
        self.h[hid] = MockHandoff(hid, m['objective'])
        return self.h[hid]
    def get_all(self): return list(self.h.values())
    def get_proposal(self, id): return self.h.get(id)
    def update_proposal(self, id, u): 
        if id in self.h: self.h[id].readiness_state = u.get('readiness_state', self.h[id].readiness_state)

handoff_manager = MockHandoffManager()

def simulate_orchestrate(message, is_intake=False, mission=None):
    authority_info = {"active": False}
    
    is_backlog_request = "SHOW MISSION HANDOFF QUEUE" in message.upper()
    is_inspect_request = "INSPECT MISSION HANDOFF" in message.upper()
    is_archive_request = "ARCHIVE MISSION HANDOFF" in message.upper()

    if is_archive_request:
        h_id_match = re.search(r"HANDOFF\s+([\w\-]+)", message, re.IGNORECASE)
        if h_id_match:
            handoff_manager.update_proposal(h_id_match.group(1), {"readiness_state": "ARCHIVED"})
        is_backlog_request = True
    
    if is_inspect_request:
        h_id_match = re.search(r"HANDOFF\s+([\w\-]+)", message, re.IGNORECASE)
        if h_id_match:
            h_prop = handoff_manager.get_proposal(h_id_match.group(1))
            if h_prop:
                mission = h_prop.model_dump()
                is_intake = True 
    
    if is_backlog_request:
        is_intake = False
    
    if is_intake and not is_inspect_request:
        handoff_manager.add_proposal(mission, {}, source="ws")

    return {"is_intake": is_intake, "mission": mission, "backlog": [h.model_dump() for h in handoff_manager.get_all()]}

# Test 1: First mission proposal
t1 = simulate_orchestrate("Propongo mision A", is_intake=True, mission={"objective": "Mision A"})
print(f"Test 1 (New): Intake={t1['is_intake']}, Backlog Size={len(t1['backlog'])}")

# Test 2: Second mission proposal
t2 = simulate_orchestrate("Propongo mision B", is_intake=True, mission={"objective": "Mision B"})
print(f"Test 2 (New): Intake={t2['is_intake']}, Backlog Size={len(t2['backlog'])}")

# Test 3: Show Backlog
t3 = simulate_orchestrate("SHOW MISSION HANDOFF QUEUE")
print(f"Test 3 (Queue): Intake={t3['is_intake']}, Backlog Status={[h['readiness_state'] for h in t3['backlog']]}")

# Test 4: Inspect 1
t4 = simulate_orchestrate("INSPECT MISSION HANDOFF 1")
print(f"Test 4 (Inspect 1): Intake={t4['is_intake']}, Mission Obj={t4['mission']['objective']}")

# Test 5: Archive 2
t5 = simulate_orchestrate("ARCHIVE MISSION HANDOFF 2")
print(f"Test 5 (Archive 2): Intake={t5['is_intake']}, Backlog Status={[h['readiness_state'] for h in t5['backlog']]}")
