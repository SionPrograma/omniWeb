import sqlite3
import os

db_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\omniweb.db"

def verify_schema():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='governance_rebase_recommendations'")
        table = cursor.fetchone()
        
        if table:
            print("✅ Table 'governance_rebase_recommendations' exists.")
            # Check columns
            cursor.execute("PRAGMA table_info(governance_rebase_recommendations)")
            cols = [c[1] for c in cursor.fetchall()]
            print(f"Columns: {cols}")
        else:
            print("❌ Table 'governance_rebase_recommendations' NOT found!")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_schema()
