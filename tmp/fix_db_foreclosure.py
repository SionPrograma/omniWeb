import sys
import os
sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

with set_chip_context("core"):
    conn = db_manager.get_connection()
    try:
        conn.execute("ALTER TABLE mission_handoffs ADD COLUMN foreclosure TEXT")
        conn.commit()
        print("Success: foreclosure column added.")
    except Exception as e:
        print(f"Bypassing or error: {e}")
