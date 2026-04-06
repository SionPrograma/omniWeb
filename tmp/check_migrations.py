import sys
import os
sys.path.append(os.getcwd())
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

with set_chip_context("core"):
    conn = db_manager.get_connection()
    rows = conn.execute("SELECT filename FROM system_migrations").fetchall()
    for row in rows:
        print(row["filename"])
