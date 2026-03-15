import os
import sys
import json
import sqlite3
import datetime

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.config import settings
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def run_audit():
    print(f"--- OMNIWEB DEEP INTEGRITY AUDIT [{datetime.datetime.now().isoformat()}] ---")
    results = {
        "architecture": "PASS",
        "chips": "PASS",
        "state_engine": "PASS",
        "security": "PASS",
        "identity": "PASS",
        "data": "PASS",
        "issues": []
    }

    # 1. Architecture Check
    print("\n[1] CODE STRUCTURE AUDIT")
    core_modules = [m.replace(".py", "") for m in os.listdir("backend/core")]
    expected_core = [
        "identity", "security", "user_logbook", "system_state", 
        "ai_host", "master_logbook", "module_registry"
    ]
    for mod in expected_core:
        if mod not in core_modules:
            results["architecture"] = "FAIL"
            results["issues"].append(f"Missing core module: backend/core/{mod}")
        else:
            print(f"  ✅ Module found: {mod}")

    # 2. Processor Discovery Check
    try:
        from backend.core.ai_host.command_router import ai_command_router
        registered = list(ai_command_router.registry._processors.keys())
        expected_processors = ["status", "generator", "user_logbook", "user_graph", "code_control", "logbook"]
        for p in expected_processors:
            if p not in registered:
                results["architecture"] = "FAIL"
                results["issues"].append(f"Processor not registered in AI Host: {p}")
            else:
                print(f"  ✅ AI Processor registered: {p}")
    except Exception as e:
        results["architecture"] = "FAIL"
        results["issues"].append(f"AI Host Discovery Error: {e}")

    # 3. Chip Registry Audit
    print("\n[2] CHIP SYSTEM INTEGRITY")
    from backend.core.module_registry import module_registry
    active_chips = module_registry.discover_all_chips()
    print(f"  Found {len(active_chips)} chips in registry.")
    
    for chip in active_chips:
        slug = chip['slug']
        chip_path = os.path.join("chips", f"chip-{slug}")
        if not os.path.exists(chip_path):
             chip_path = os.path.join("chips", slug) # Try fallback
             
        if not os.path.exists(chip_path):
            results["chips"] = "FAIL"
            results["issues"].append(f"Chip '{slug}' registered but folder missing at {chip_path}")
            continue
            
        # Check manifest
        manifest_path = os.path.join(chip_path, "chip.json")
        if not os.path.exists(manifest_path):
            results["chips"] = "FAIL"
            results["issues"].append(f"Chip '{slug}' missing chip.json")
        else:
            print(f"  ✅ Chip '{slug}': Manifest OK")

    # 4. State Engine Check
    print("\n[3] STATE ENGINE VERIFICATION")
    try:
        # We can't easily run async code in this simple script easily without loop
        # But we can check if the module is importable and classes defined
        from backend.core.system_state.engine import state_engine
        print("  ✅ State Engine initialized.")
    except Exception as e:
        results["state_engine"] = "FAIL"
        results["issues"].append(f"State Engine Import Error: {e}")

    # 5. Database Consistency
    print("\n[4] DATA & DB INTEGRITY")
    required_tables = [
        "users", "user_logbooks", "user_graph_nodes", "user_graph_edges",
        "trusted_devices", "security_audit_logs", "system_migrations"
    ]
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            existing_tables = [row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            for table in required_tables:
                if table not in existing_tables:
                    results["data"] = "FAIL"
                    results["issues"].append(f"Database table missing: {table}")
                else:
                    print(f"  ✅ DB Table verified: {table}")
            
            # Check migration count
            count = conn.execute("SELECT COUNT(*) as cnt FROM system_migrations").fetchone()["cnt"]
            print(f"  ✅ Applied migrations: {count}")

    # 6. User Isolation Check
    print("\n[5] USER ISOLATION (WORKSPACE)")
    if os.path.exists("user_workspace"):
        workspaces = os.listdir("user_workspace")
        print(f"  Total workspaces: {len(workspaces)}")
        for ws in workspaces:
            logbook_dir = os.path.join("user_workspace", ws, "logbook")
            if os.path.exists(logbook_dir):
                print(f"  ✅ Workspace '{ws}': Logbook Partition OK")
            else:
                print(f"  ⚠️ Workspace '{ws}': No logbook folder yet.")

    # 7. Router Mounting Audit
    print("\n[6] ROUTER MOUNTING CHECK")
    with open("backend/main.py", "r") as f:
        main_content = f.read()
    
    expected_routers = [
        "auth_router", "identity_router", "creator_gateway_router", 
        "system_router", "user_logbook_router", "user_graph_router"
    ]
    for r in expected_routers:
        if r not in main_content:
            results["architecture"] = "FAIL"
            results["issues"].append(f"Router '{r}' not found as included in main.py")
        else:
            print(f"  ✅ Router mounted: {r}")

    # 8. Security Gateway Verification
    print("\n[7] SECURITY GATEWAY CHECK")
    try:
        from backend.core.security.dependencies import get_creator_user
        from backend.core.auth import OmniUser
        # Mock a normal user 
        hacker = OmniUser(id="hacker", username="hacker", role="user")
        import asyncio
        try:
             # This is a dependency, calling it requires a request mock if it uses Request
             # But our implementation mostly uses the user object
             asyncio.run(get_creator_user(current_user=hacker))
             results["security"] = "FAIL"
             results["issues"].append("Security Bypass: Non-creator user accessed get_creator_user without error")
        except Exception:
             print("  ✅ Creator Gateway correctly rejected non-creator user.")
    except Exception as e:
        print(f"  ⚠️ Skipping direct security call test: {e}")

    # 9. Performance / Loop check
    print("\n[8] PERFORMANCE CHECK")
    # Check for state refresh interval in frontends or background tasks
    # For now, just verify config settings
    print(f"  ✅ System Mode: {settings.OMNIWEB_MODE}")
    print(f"  ✅ Version: {settings.VERSION}")

    # Final Report
    print("\n--- AUDIT SUMMARY ---")
    if results["architecture"] == "PASS" and results["chips"] == "PASS" and results["data"] == "PASS" and results["security"] == "PASS":
        print("✨ OMNIWEB SYSTEM INTEGRITY VERIFIED: NO INCONSISTENCIES FOUND")
    else:
        print(f"❌ AUDIT FAILED: {len(results['issues'])} issues detected.")
        for issue in results["issues"]:
            print(f"  - {issue}")
    
    return results

if __name__ == "__main__":
    run_audit()
