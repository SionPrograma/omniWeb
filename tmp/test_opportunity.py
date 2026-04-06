import asyncio
import sys
import json
import uuid
from datetime import datetime

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.ai_host.memory.opportunity_scanner import opportunity_scanner
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
import backend.core.permissions

def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

async def test_opportunities():
    print("\n--- TACTICAL OPPORTUNITY SCANNER TEST ---")
    
    with set_chip_context("core"):
        # 1. SETUP EVIDENCE
        print("Setup: Injecting friction evidence...")
        with db_manager.get_connection() as conn:
            # Rebase hotspot: 5 mutations in 'auth_engine'
            # builder_mutations uses REAL unix timestamps
            for i in range(5):
                conn.execute("INSERT INTO builder_mutations (id, module_id, status, timestamp) VALUES (?, ?, ?, strftime('%s', 'now'))", (str(uuid.uuid4()), "auth_engine", "COMPLETED"))
            
            # Governance friction: 3 blocks in same gate
            payload = json.dumps({"reason": "Test Block", "authority": "AUTHORITY_PIN"})
            for i in range(3):
                conn.execute("INSERT INTO atomic_push_forensics (push_id, event_type, payload, actor) VALUES (?, ?, ?, ?)", ("test-push", "STEP_BLOCKED", payload, "creator"))
            conn.commit()

        # 2. SCAN
        print("\nScanning for opportunities...")
        opps = opportunity_scanner.scan_for_opportunities()
        for o in opps:
            print(f"Detected: {o.type} on {o.surface} (Score: {o.score:.2f})")
            print(f"  Rationale: {o.rationale}")

        assert len(opps) >= 2
        print("Opportunity detection: PASSED")

        # 3. CONVERT
        hotspot_opp = next(o for o in opps if o.type == "REBASE_HOTSPOT")
        print(f"\nConverting opportunity {hotspot_opp.opportunity_id[:6]} to mission...")
        mission = opportunity_scanner.convert_to_mission(hotspot_opp.opportunity_id)
        
        assert mission is not None
        assert mission["source_type"] == "opportunity_scanner"
        print(f"Success: Mission created: {mission['objective'][:40]}...")
        print("Conversion flow: PASSED")

        # 4. ANTI-SPAM (Multiple scans should return same count/grouped)
        print("\nVerifying anti-spam/grouping...")
        opps_v2 = opportunity_scanner.scan_for_opportunities()
        # Should not double count the surface
        auth_opps = [o for o in opps_v2 if o.surface == "auth_engine"]
        assert len(auth_opps) == 1
        print("Anti-spam/Grouping: PASSED")

        print("\nAll opportunity validations SUCCESSFUL.")

        # Cleanup
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM builder_mutations WHERE module_id = 'auth_engine'")
            conn.execute("DELETE FROM atomic_push_forensics WHERE push_id = 'test-push'")
            conn.commit()
        if mission:
            handoff_manager.delete_proposal(mission["handoff_id"])

if __name__ == "__main__":
    asyncio.run(test_opportunities())
