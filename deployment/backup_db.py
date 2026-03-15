import os
import sys
from backend.core.database import db_manager

def main():
    print("Starting DB backup...")
    try:
        backup_path = db_manager.backup_db()
        print(f"Backup created at: {backup_path}")
        if os.path.exists(backup_path):
            print("Verification: Backup file exists.")
        else:
            print("Verification: Backup file NOT found!")
            sys.exit(1)
    except Exception as e:
        print(f"Error during backup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
