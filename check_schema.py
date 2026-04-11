
import sqlite3
db_path = "backend/data/omniweb.db"
conn = sqlite3.connect(db_path)
tables = ["roadmap_branches", "mission_handoffs", "system_missions"]
for t in tables:
    c = conn.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in c.fetchall()]
    print(f"{t}: {cols}")
conn.close()
