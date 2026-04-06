import sqlite3
import json
conn = sqlite3.connect('backend/data/omniweb.db')
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM system_events ORDER BY id DESC LIMIT 5").fetchall()
for r in rows:
    print(dict(r))
conn.close()
