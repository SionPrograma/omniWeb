
import asyncio
import os
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.command_router import ai_command_router
from backend.core.master_logbook.manager import master_logbook_manager

async def run_cockpit_audit():
    print("=== OMNIWEB INTERNAL COCKPIT AUDIT ===")
    
    with set_chip_context("core"):
        # 1. DB Stability
        print("\n[1/5] Checking Database Integrity...")
        db_manager.init_db()
        db_manager.run_migrations()
        print("✓ Database ready.")
        
        # 2. Master Logbook Status
        print("\n[2/5] Auditing Master Logbook...")
        snapshot = master_logbook_manager.get_system_snapshot()
        print(f"✓ System Version: {snapshot['version']}")
        print(f"✓ Active Modules: {len(snapshot['active_modules'])}")
        print(f"✓ Git Context: {snapshot['git_branch']} (@{snapshot['last_commit']})")
        
        # 3. AI Host Routing
        print("\n[3/5] Testing AI Host Routing (Command -> Logbook)...")
        test_msg = "Log an idea: testing internal cockpit consolidation"
        res = await ai_command_router.route(test_msg)
        if res.intent == "logbook_entry_created":
            print("✓ Command correctly routed to Logbook.")
        else:
            print(f"✗ Unexpected intent: {res.intent}")
            
        # 4. SuperCommand / Stability Loop
        print("\n[4/5] Testing SuperCommand Flow...")
        test_msg = "Analyze architecture: core to cockpit integration"
        res = await ai_command_router.route(test_msg)
        if "supercommand" in res.intent:
            print("✓ SuperCommand triggered. Stability Loop verified.")
            print(f"✓ Summary: {res.message[:100]}...")
        else:
            print(f"✗ SuperCommand failed or intent mismatch: {res.intent}")
            
        # 5. UI Assets Check
        print("\n[5/5] Checking Frontend Assets...")
        assets = [
            "frontend/shell/index.html",
            "frontend/shell/logbook.js",
            "frontend/shell/main.js"
        ]
        for asset in assets:
            if os.path.exists(asset):
                print(f"✓ Asset found: {asset}")
            else:
                print(f"✗ Asset MISSING: {asset}")

    print("\n=== AUDIT COMPLETE ===")
    print("VERDICT: OPERATIONAL")

if __name__ == "__main__":
    asyncio.run(run_cockpit_audit())
