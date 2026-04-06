import sqlite3
import sys

db_path = r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\omniweb.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

def check(table):
    print(f"\n--- Schema for {table} ---")
    try:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        for row in cursor.fetchall():
            print(dict(row))
    except Exception as e:
        print(f"Error: {e}")

check("builder_mutations")
check("atomic_push_forensics")
conn.close()
