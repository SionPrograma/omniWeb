import sys
import os
import asyncio
import logging

# Ensure the root of the project is in the Python path
sys.path.append(os.getcwd())

from backend.core.governance.system_auditor import engineering_auditor

logging.basicConfig(level=logging.INFO)

async def main():
    print("\n" + "="*50)
    print("OMNIWEB ENGINEERING GOVERNANCE AUDIT")
    print("="*50 + "\n")
    
    # Run audit
    report = await engineering_auditor.run_full_audit()
    
    print(f"OVERALL STATUS: {report['stability_status']}")
    print("-" * 30)
    
    for check in report['checks']:
        color = "✅" if check['status'] == "PASS" else "❌"
        print(f"{color} [{check['sector'].upper()}] {check['check']}: {check['status']} - {check['details']}")
    
    print("\n" + "="*50)
    if report['stability_status'] == "SYSTEM STABLE":
        print("ENGINEERING GOVERNANCE MODE ACTIVE")
    else:
        print("ATTENTION: CORE STABILITY ISSUES DETECTED")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
