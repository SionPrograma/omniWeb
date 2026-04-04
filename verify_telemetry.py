import asyncio
import uuid
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.memory.mission_telemetry import mission_telemetry
from backend.core.system_state.engine import state_engine

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

async def verify_telemetry():
    print("--- INICIANDO VALIDACIÓN DE TELEMETRÍA ---")
    
    with set_chip_context("core"):
        # 0. Asegurar base de datos
        db_manager.run_migrations()
        
        # 1. Crear una misión de prueba
        mission = mission_manager.create_mission(
            goal="Validación de Telemetría Crítica"
        )
        m_id = mission.mission_id
        mission_manager.active_mission = mission
        
        print(f"Misión creada y puesta en foco: {m_id}")
        
        # 2. Simular eventos
        print("Registrando eventos simulados...")
        mission_telemetry.record_event(m_id, "step_started", "Iniciando auditoría de zona...", step_id="1.1")
        mission_telemetry.record_event(m_id, "step_completed", "Auditoría completada sin novedades.", step_id="1.1")
        mission_telemetry.record_event(m_id, "warning", "Inestabilidad detectada en capa de red", severity="WARNING")
        mission_telemetry.record_event(m_id, "rescue_triggered", "Shadow Swarm activado para rescate quirúrgico", severity="CRITICAL")
        
        # 3. Forzar actualización de estado del sistema
        print("Actualizando estado del sistema...")
        state = await state_engine.update_state()
    
    # 4. Verificar presencia en el estado
    print("\nResultados de Agregación:")
    print(f"Eventos en misión activa ({len(state.mission_events)}):")
    for e in state.mission_events:
        print(f"  [{e['timestamp']}] {e['severity']} - {e['event_type']}: {e['message']}")
        
    print(f"\nPulse del Portfolio ({len(state.portfolio_pulse)}):")
    for e in state.portfolio_pulse:
        print(f"  [{e['mission_id'][:8]}] {e['event_type']}: {e['message']}")

    print("\n--- VALIDACIÓN COMPLETADA ---")

if __name__ == "__main__":
    asyncio.run(verify_telemetry())
