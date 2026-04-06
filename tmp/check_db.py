from backend.core.database import db_manager
try:
    conn = db_manager.get_connection()
    cols = conn.execute("PRAGMA table_info(mission_schedules)").fetchall()
    for col in cols:
        print(f"Column: {col['name']}")
    
    # Try to add column if not exists
    if not any(col['name'] == 'suggestions' for col in cols):
        print("Adding column suggestions...")
        conn.execute("ALTER TABLE mission_schedules ADD COLUMN suggestions TEXT")
        conn.commit()
except Exception as e:
    print(f"Error: {e}")
