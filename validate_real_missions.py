
import sys
import os
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

# Ajustar paths para importar desde el raíz
sys.path.append(os.getcwd())

# Configurar logs mínimos para ver qué pasa
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VALIDATION")

from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.processors.base import AICommandResponse

async def run_validation():
    print("\n--- INICIANDO VALIDACIÓN REAL DE MISSIONSTATE (PULIDA) ---")
    
    # 0. Limpieza previa (Oregimentado por permisos)
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM system_missions")
            conn.commit()
    
    mock_command_router = MagicMock()
    # Mock de registro de procesadores
    mock_chat_proc = AsyncMock()
    mock_chat_proc.process.side_effect = lambda msg, context=None: asyncio.Future()
    # Para simplificar el mock de un coroutine que retorna un objeto
    async def mock_chat_return(msg, context=None):
        return AICommandResponse(intent="greeting", status="success", message="¡Hola! Soy Omni. ¿En qué puedo ayudarte?")
    
    mock_chat_proc.process = mock_chat_return
    mock_command_router.registry.get_processor.return_value = mock_chat_proc
    
    router = BrainRouter(mock_command_router)
    
    user_context = {"user_id": "creator_01"}
    
    with set_chip_context("core"):
        # 1. CREACIÓN DE MISIÓN
        print("\n1. PROBANDO CREACIÓN [Analiza el chip logbook]")
        res1 = await router.process("Analiza el chip logbook", context=user_context)
        
        m1 = mission_manager.get_active_mission()
        if m1 and m1.status == MissionStatus.OPEN:
            print(f"SUCCESS: Misión creada: {m1.active_goal}")
        else:
            print(f"FAILURE: No se detectó misión activa. Status: {m1.status if m1 else 'None'}")
            return

        # 2. INTERRUPCIÓN CASUAL
        print("\n2. PROBANDO INTERRUPCIÓN [Hola, todo bien?]")
        res2 = await router.process("Hola, todo bien?", context=user_context)
        
        m2 = mission_manager.get_active_mission()
        if m2 and m2.status == MissionStatus.PAUSED:
            print(f"SUCCESS: Misión pausada correctamente.")
            print(f"   Respuesta: {res2.message}")
        else:
            print(f"FAILURE: La misión no se pausó. Status: {m2.status if m2 else 'None'}")
        
        # 3. REHIDRATACIÓN (Reinicio simulado)
        print("\n3. PROBANDO REINICIO (Simulando nueva instancia de sistema)")
        mission_manager.active_mission = None # Forzamos recarga desde DB
        m_rehydrated = mission_manager.get_active_mission()
        if m_rehydrated and m_rehydrated.mission_id == m1.mission_id:
            print(f"SUCCESS: Misión rehidratada desde DB: {m_rehydrated.active_goal}")
        else:
            print(f"FAILURE: Falló la rehidratación persistente.")
            return

        # 4. RETOMA BREVE
        print("\n4. PROBANDO RETOMA [seguí]")
        res3 = await router.process("seguí", context=user_context)
        
        m3 = mission_manager.get_active_mission()
        # NOTA: En el primer paso del mock analysis, puede que quede en WAITING_CONFIRMATION si es un flush/patch
        # Pero MissionStatus debería volver a OPEN antes de procesar
        if m3 and m3.status == MissionStatus.OPEN:
            print(f"SUCCESS: Misión retomada. Volvió a estado OPEN.")
            if "MISIÓN ACTIVA" in res3.message:
                print(f"   Voz Oficial: Bloque técnico detectado correctamente.")
            else:
                print(f"   WARNING: El mensaje no parece mencionar la misión: {res3.message[:50]}...")
        else:
            print(f"FAILURE: No se retomó la misión correctamente. Status: {m3.status if m3 else 'None'}")

        # 5. CIERRE CORRECTO
        print("\n5. PROBANDO CIERRE (Completando pasos)")
        pending = list(m3.pending_steps)
        for step in pending:
            mission_manager.update_mission_step(step)
        
        m4 = mission_manager.get_active_mission()
        if not m4 or m4.status == MissionStatus.COMPLETED:
            print(f"SUCCESS: Misión completada y cerrada.")
        else:
            print(f"FAILURE: La misión sigue abierta. Status: {m4.status}")

        # 6. SALUD POST-CIERRE
        print("\n6. PROBANDO CHAT POST-CIERRE [Cómo va todo?]")
        res4 = await router.process("Cómo va todo?", context=user_context)
        if "MISIÓN ACTIVA" not in res4.message:
            print(f"SUCCESS: Chat limpio de fantasmas técnicos.")
        else:
            print(f"FAILURE: Contaminación detectada.")

    print("\n--- VALIDACIÓN FINALIZADA ---")

if __name__ == "__main__":
    asyncio.run(run_validation())
