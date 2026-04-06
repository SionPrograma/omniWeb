import sys
import os
sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

with set_chip_context("core"):
    conn = db_manager.get_connection()
    cursor = conn.execute("PRAGMA table_info(system_mission_telemetry)")
    for col in cursor.fetchall():
        print(dict(col))
