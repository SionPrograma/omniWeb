import sqlite3
import os

DB_PATH = 'backend/data/omniweb.db'

def diagnose():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    print(f"VERIFYING DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [x['name'] for x in c.fetchall()]
    print(f"Tables Found ({len(tables)}): {tables}")
    
    # Check System User
    SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'
    c.execute("SELECT * FROM users WHERE id = ?", (SYSTEM_UUID,))
    user = c.fetchone()
    if user:
        print(f"System User Found: SUCCESS (id={user['id']}, username={user['username']})")
    else:
        print(f"System User Found: FAILED (id={SYSTEM_UUID} is missing)")
        
    # Check total users
    c.execute("SELECT count(*) as count FROM users")
    count = c.fetchone()['count']
    print(f"Total Users: {count}")

    # Check the security_audit_logs table structure
    if 'security_audit_logs' in tables:
        c.execute("PRAGMA foreign_key_list(security_audit_logs)")
        fks = c.fetchall()
        print(f"FKs for security_audit_logs: {[dict(f) for f in fks]}")

    conn.close()

if __name__ == "__main__":
    diagnose()
