from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

with set_chip_context("core"):
    with db_manager.get_connection() as conn:
        with open("backend/data/migrations/103_exception_tracking.sql") as f:
            conn.executescript(f.read())
        print("Migration 103 applied successfully.")
