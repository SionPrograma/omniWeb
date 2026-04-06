import sys
import os
sys.path.append(os.getcwd())
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

with set_chip_context("core"):
    conn = db_manager.get_connection()
    tables = [row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"Tables: {', '.join(tables)}")
    if "branch_arbitrations" in tables:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(branch_arbitrations)").fetchall()]
        print(f"Branch Arbitrations Columns: {', '.join(columns)}")
