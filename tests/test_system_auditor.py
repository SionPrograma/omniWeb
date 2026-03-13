import asyncio
import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.system_auditor.auditor import auditor
from backend.core.system_auditor.models import AuditStatus
from backend.core.permissions import set_chip_context

async def test_audit():
    print("🚀 Starting OmniWeb System Audit Test...")
    
    try:
        # Run audit (it already has the context inside, but let's be safe)
        report = await auditor.run_full_audit()
        
        print("\n--- AUDIT REPORT SUMMARY ---")
        print(f"Timestamp: {report.timestamp}")
        print(f"Status: {report.overall_status.value}")
        print(f"Summary: {report.summary}")
        
        print("\n--- ISSUES ---")
        if not report.issues:
            print("No issues found! System is healthy.")
        for issue in report.issues:
            print(f"[{issue.sector.value}] {issue.level.value}: {issue.message}")
            if issue.details:
                print(f"  Details: {issue.details}")
                
        print("\n--- METRICS ---")
        for k, v in report.metrics.items():
            print(f"{k}: {v}")
            
        # Verify Logbook Integration (NEEDS CORE CONTEXT TO ACCESS DB)
        with set_chip_context("core"):
            from backend.core.master_logbook.manager import master_logbook_manager
            from backend.core.master_logbook.models import EntryType, MasterLogbookFilter
            
            filters = MasterLogbookFilter(type=EntryType.SYSTEM_AUDIT)
            entries = master_logbook_manager.get_entries(filters=filters, limit=1)
            
            if entries:
                print(f"\n✅ Logbook Integration Verified. Latest entry ID: {entries[0].id}")
                print(f"Entry Preview: {entries[0].content[:100]}...")
            else:
                print("\n❌ Logbook Integration Failed. No audit entry found.")
            
    except Exception as e:
        print(f"\n❌ Audit Execution Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_audit())
