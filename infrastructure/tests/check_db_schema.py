import sqlite3
import os

DB_PATH = "backend/data/omniweb.db"

def check_db_schema():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"--- DATABASE SCHEMA AUDIT: {DB_PATH} ---")
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    print(f"Tables found: {tables}")

    for table in tables:
        print(f"\nSchema for table '{table}':")
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            print(f"   - {col['name']} ({col['type']})")
    
    # Check migrations
    if "system_migrations" in tables:
        print("\nApplied Migrations:")
        cursor.execute("SELECT * FROM system_migrations")
        for row in cursor.fetchall():
            print(f"   - {row['filename']} (Applied at: {row['applied_at']})")

    conn.close()

if __name__ == "__main__":
    check_db_schema()
