
import sys
import os
sys.path.append(os.path.abspath(os.getcwd()))

try:
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        db_manager.run_migrations()
    print("Migrations applied successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
