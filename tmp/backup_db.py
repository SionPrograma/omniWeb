from backend.core.database import db_manager
import os

try:
    backup_path = db_manager.backup_db()
    if os.path.exists(backup_path):
        print(f"DATABASE_BACKUP_SUCCESS: {backup_path}")
    else:
        print(f"DATABASE_BACKUP_FAILURE: Backup file not found at {backup_path}")
except Exception as e:
    print(f"DATABASE_BACKUP_ERROR: {e}")
