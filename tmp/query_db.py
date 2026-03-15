
import sqlite3
import os

db_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\omniweb.db"

def query():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT id, type, content, timestamp FROM master_logbook ORDER BY timestamp DESC LIMIT 5")
    rows = cursor.fetchall()
    
    print(f"Recent entries in master_logbook:")
    for row in rows:
        print(f"ID: {row['id']} | Type: {row['type']} | Content: {row['content'][:50]}... | Time: {row['timestamp']}")
    conn.close()

if __name__ == "__main__":
    query()
