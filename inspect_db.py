import sqlite3
import json

def inspect():
    conn = sqlite3.connect('backend/omni.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("PRAGMA table_info(system_missions)")
    cols = cursor.fetchall()
    print("--- MISSION TABLE INFO ---")
    for c in cols:
        print(f"{c['name']} ({c['type']})")
    
    print("\n--- ACTIVE MISSIONS ---")
    cursor = conn.execute("SELECT mission_id, active_goal, status, context_snap FROM system_missions LIMIT 5")
    rows = cursor.fetchall()
    for r in rows:
        print(f"ID: {r['mission_id']} | Goal: {r['active_goal']} | Status: {r['status']}")
        try:
            snap = json.loads(r['context_snap'])
            print(f"  Drifts: {len(snap.get('drift_alerts', []))}")
        except:
            print("  Snap error")

if __name__ == "__main__":
    inspect()
