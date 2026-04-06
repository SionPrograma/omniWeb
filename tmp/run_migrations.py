import sys
import os
sys.path.append(os.getcwd())
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

with set_chip_context("core"):
    print("Running migrations...")
    db_manager.run_migrations()
    print("Migrations complete.")
