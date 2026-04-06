import sys
import os
sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

with set_chip_context("core"):
    conn = db_manager.get_connection()
    cursor = conn.execute("PRAGMA foreign_key_list(system_mission_telemetry)")
    for fk in cursor.fetchall():
        print(dict(fk))
