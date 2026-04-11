import sqlite3
import json
import os

db_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\omniweb.db"
if not os.path.exists(db_path):
    print(f"Error: DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
try:
    rows = conn.execute("SELECT * FROM governance_decision_ledger WHERE decision_type LIKE 'CATALYST_%' ORDER BY created_at DESC LIMIT 10").fetchall()
    for r in rows:
        print(f"--- {r['decision_type']} ({r['target_id']}) ---")
        print(f"Rationale: {r['rationale']}")
        try:
            data = json.loads(r['evidence_refs'])
            print(json.dumps(data, indent=2))
        except:
            print(f"Raw Ref: {r['evidence_refs']}")
        print("\n")
except Exception as e:
    print(f"Query error: {e}")
finally:
    conn.close()
