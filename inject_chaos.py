import sqlite3
import json
import uuid
from datetime import datetime

def inject_chaos():
    conn = sqlite3.connect('backend/omni.db')
    conn.row_factory = sqlite3.Row
    
    # 1. Create a Mission if none exists or get latest
    cursor = conn.execute("SELECT mission_id FROM system_missions ORDER BY updated_at DESC LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("Creando misión para el test...")
        mid = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO system_missions (mission_id, active_goal, status, context_snap, parameters, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mid, "Validación de Estrés HUD", "OPEN", json.dumps({}), json.dumps({}), datetime.now().isoformat()))
    else:
        mid = row['mission_id']
        print(f"Usando misión existente: {mid}")

    # 2. ESCENARIO: DERIVA CRÍTICA
    snap = {
        "drift_alerts": [
            {
                "type": "COGNITIVE_DRIFT",
                "severity": "CRITICAL",
                "message": "!!! DERIVA CRÍTICA DETECTADA EN RUNTIME !!!",
                "suggestion": "Reorientar foco táctico inmediatamente.",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "is_healing": True
    }
    
    # 3. ESCENARIO: AUTHORITY
    params = {
        "authority_session": {
            "active": True,
            "expires_at": (datetime.now().isoformat())
        }
    }

    conn.execute("""
        UPDATE system_missions 
        SET context_snap = ?, parameters = ?, status = ?, updated_at = ?
        WHERE mission_id = ?
    """, (json.dumps(snap), json.dumps(params), "BLOCKED", datetime.now().isoformat(), mid))
    
    # 4. ALERTA PARALELA
    conn.execute("""
        INSERT INTO system_missions (mission_id, active_goal, status, updated_at)
        VALUES (?, ?, ?, ?)
    """, (str(uuid.uuid4()), "Misión Fantasma Bloqueada", "BLOCKED", datetime.now().isoformat()))

    conn.commit()
    print(f"Caos inyectado en misión {mid}. El HUD debería reflejar estado CRITICAL, HEALING y 1 Alerta Paralela.")

if __name__ == "__main__":
    inject_chaos()
