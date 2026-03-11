
import sys
import os

# Ensure backend is in path
sys.path.append('c:/Users/Propietario/Desktop/plan actual/07-proyectosGrandes/01-omniweb')

from backend.core.database import db_manager

try:
    backup_path = db_manager.backup_db()
    print(f"BACKUP_SUCCESS: {backup_path}")
except Exception as e:
    print(f"BACKUP_FAILED: {e}")
    sys.exit(1)
