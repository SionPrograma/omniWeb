import os
import json
import datatime

def audit_repo():
    print("--- OMNIWEB ARCHITECTURE AUDIT ---")
    print(f"Timestamp: {datetime.datetime.now()}")
    
    components = {
        "Core": "backend/core",
        "Chips": "chips",
        "Shell": "frontend/shell",
        "Docs": "docs"
    }
    
    for name, path in components.items():
        exists = os.path.exists(path)
        status = "PASSED" if exists else "FAILED"
        print(f"[{status}] {name} component located at {path}")

if __name__ == "__main__":
    import datetime # Fix typo
    audit_repo()
