import sqlite3
import json
import os

db_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\omniweb.db"

def query_lineage():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT project_slug FROM ai_host_project_lineage").fetchall()
        for row in rows:
            print(f"Slug: {row['project_slug']}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    query_lineage()
