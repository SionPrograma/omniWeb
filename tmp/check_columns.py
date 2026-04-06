import sys
import os
sys.path.append(os.getcwd())
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

with set_chip_context("core"):
    conn = db_manager.get_connection()
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(mission_handoffs)").fetchall()]
    print(", ".join(columns))
