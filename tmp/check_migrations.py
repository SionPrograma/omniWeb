import sys
import os
import sqlite3

# Ensure the root of the project is in the Python path
sys.path.append(os.getcwd())

from backend.core.config import settings

def main():
    db_path = settings.DATABASE_URL
    print(f"Checking migrations in {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT filename FROM system_migrations").fetchall()
        print("Applied migrations:")
        for row in rows:
            print(f" - {row['filename']}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
