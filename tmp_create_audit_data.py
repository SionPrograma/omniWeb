import sys
import os
import uuid
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.ai_host.memory.mission_manager import MissionManager
from backend.core.ai_host.memory.mission_models import MissionState, MissionStatus

def populate():
    mm = MissionManager()

    # 1. Mission ALIGNED
    m1 = mm.create_mission("Optimizar base de datos de telemetría")
    m1.status = MissionStatus.RUNNING
    m1.multimodal_history = [
        {
            "id": str(uuid.uuid4()),
            "event": "INITIAL_CAPTURE",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"layer": "database", "description": "Lentitud en queries de agregación", "confidence": 0.9}
        }
    ]
    mm.save_mission(m1)
    print(f"Created Aligned Mission: {m1.mission_id}")

    # 2. Mission DRIFTING
    m2 = mm.create_mission("Implementación de Sharding en Clúster")
    m2.status = MissionStatus.RUNNING
    m2.multimodal_history = [
        {
            "id": str(uuid.uuid4()),
            "event": "INITIAL_CAPTURE",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"layer": "infrastructure/sharding", "description": "Distribución de carga", "confidence": 0.8}
        },
        {
            "id": str(uuid.uuid4()),
            "event": "FOCUS_SHIFT",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"layer": "frontend/ui", "description": "Cambiando a arreglar botones de dashboard", "confidence": 0.7},
            "creator_comment": "Me distraje con un bug visual"
        }
    ]
    # Injected drift score via history above should be calculated by analyze_cognitive_drift
    mm.save_mission(m2)
    print(f"Created Drifting Mission: {m2.mission_id}")

    # 3. Mission HEALING
    m3 = mm.create_mission("Sincronización de Nodos Edge")
    m3.status = MissionStatus.RUNNING
    m3.multimodal_history = [
        {
            "id": str(uuid.uuid4()),
            "event": "INITIAL_CAPTURE",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"layer": "network/edge", "description": "Latencia alta en sincronización", "confidence": 0.85}
        },
        {
            "id": str(uuid.uuid4()),
            "event": "AUTO_RECOVERY",
            "timestamp": datetime.now().isoformat(),
            "action_type": "RESTORE_CONTEXT",
            "message": "Auto-recuperación de contexto tras desconexión de nodo"
        }
    ]
    mm.save_mission(m3)
    print(f"Created Healing Mission: {m3.mission_id}")

if __name__ == "__main__":
    populate()
