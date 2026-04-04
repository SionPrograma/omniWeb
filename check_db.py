
import sqlite3
import json

conn = sqlite3.connect('backend/omni.db')
cursor = conn.cursor()

goal = 'Validación de Visual Diff'
cursor.execute("SELECT multimodal_history FROM system_missions WHERE active_goal = ?", (goal,))
row = cursor.fetchone()

if row:
    history = json.loads(row[0])
    print(json.dumps(history, indent=2))
else:
    print("Mission not found")

conn.close()
