import asyncio
import sys
import os
from unittest.mock import MagicMock

# Ajustar path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Mock environment if needed
os.environ["OMNIWEB_ENV"] = "test"

from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus

# Instanciamos el router manualmente para el test
brain_router = BrainRouter(ai_command_router)

async def run_test():
    print("\n--- INICIANDO VALIDACIÓN DE CONTINUIDAD DE MISIÓN (MISSIONSTATE) ---")

    # Limpiar DB de misiones previas para el test
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM system_missions")
            conn.commit()

    # 1. CREACIÓN (Orden técnica)
    print("\nPROBANDO (1): [AUDITÁ SISTEMA] -> Debería crear mision")
    res1 = await brain_router.process("auditá sistema", 
                                     context={"user_id": "test_dev"}, 
                                     runtime_context=MagicMock())
    
    m1 = mission_manager.get_active_mission()
    if m1:
        print(f"SUCCESS: MISSION CREATED: {m1.active_goal}")
        print(f"SUCCESS: STATUS: {m1.status.value}")
    else:
        print(f"FAILURE: Mission not created.")

    # 2. PAUSA (Interrupción casual)
    print("\nPROBANDO (2): [HOLA] -> Debería ser casual sin rastro técnico")
    res2 = await brain_router.process("hola", 
                                     context={"user_id": "test_dev"}, 
                                     runtime_context=MagicMock())
    
    print(f"   [DEBUG] MSG2: {res2.message}")
    if "MISIÓN ACTIVA" not in res2.message:
        print(f"SUCCESS: CLEAN: No technical noise in chat.")
    else:
        print(f"FAILURE: Technical noise detected in casual chat.")

    # 3. RETOMA (Seguí)
    print("\nPROBANDO (3): [SEGUÍ] -> Debería reanudar la misión")
    # Limpiamos el logger local antes de retomar
    res3 = await brain_router.process("seguí", 
                                     context={"user_id": "test_dev"}, 
                                     runtime_context=MagicMock())
    
    if "MISIÓN ACTIVA" in res3.message or "Plan" in res3.message or "PLAN" in res3.message:
        print(f"SUCCESS: System resumed operational flow.")
        print(f"   Msg: {res3.message[:100]}...")
    else:
        print(f"FAILURE: Continuity not detected after 'seguí'.")

    # 4. CIERRE (Completado)
    print("\nPROBANDO (4): [ESTADO] -> Verificar cierre progresivo")
    # Simulamos que el execution controller completó pasos
    mission_manager.update_mission_step("1")
    mission_manager.update_mission_step("2") # Esto debería marcarla como COMPLETED
    
    m2 = mission_manager.get_active_mission()
    if not m2 or m2.status == MissionStatus.COMPLETED:
        print(f"SUCCESS: Mission marked as COMPLETED.")
    else:
        print(f"FAILURE: Mission still open ({m2.status.value})")

    # 5. RE-ARRANQUE (Recarga/Fuga de mision)
    print("\nPROBANDO (5): [HOLA] tras cierre -> No debería aparecer misión")
    res5 = await brain_router.process("hola", 
                                     context={"user_id": "test_dev"}, 
                                     runtime_context=MagicMock())
    if "MISIÓN ACTIVA" not in res5.message:
        print(f"SUCCESS: CLEAN: No ghost missions after completion.")
    else:
        print(f"FAILURE: Ghost mission detected.")

    print("\n--- FIN DE VALIDACIÓN ---")

if __name__ == "__main__":
    asyncio.run(run_test())
