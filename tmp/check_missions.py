import sqlite3
import json

try:
    conn = sqlite3.connect('c:/Users/Propietario/Desktop/plan actual/07-proyectosGrandes/01-omniweb/backend/data/omniweb.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    row = cursor.execute('SELECT * FROM system_missions ORDER BY updated_at DESC LIMIT 1').fetchone()
    if row:
        print(f"Mission ID: {row['mission_id']}")
        print(f"Goal: {row['active_goal']}")
        print(f"Multimodal History: {json.dumps(json.loads(row['multimodal_history']), indent=2)}")
    else:
        print("No missions found.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
