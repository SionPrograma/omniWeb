import asyncio
import sys
import os
from pathlib import Path

# Resolver la raíz del proyecto de forma robusta
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Verificar que exista la carpeta backend antes de importar
if not (PROJECT_ROOT / "backend").exists():
    print(f"ERROR: No se encontró la carpeta 'backend' en {PROJECT_ROOT}")
    sys.exit(1)

from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus

async def validate_hierarchy():
    print("--- 🌳 INICIANDO VALIDACIÓN DE JERARQUÍA ---")
    
    # 1. Crear Misión Padre
    parent = mission_manager.create_mission("PROYECTO: FORTALECIMIENTO DE SEGURIDAD L2")
    print(f"Misión Padre creada: {parent.mission_id} - {parent.active_goal}")
    
    # 2. Crear Sub-misión 1 (Auditoría)
    sub1 = mission_manager.create_sub_mission(parent.mission_id, "SUB: Auditoría de Chips Críticos", relation_type="SUB_MISSION")
    print(f"Sub-misión 1 creada: {sub1.mission_id} - {sub1.active_goal}")
    
    # 3. Crear Sub-misión 2 (Implementación)
    sub2 = mission_manager.create_sub_mission(parent.mission_id, "SUB: Parcheado de Vulnerabilidades", relation_type="SUB_MISSION")
    print(f"Sub-misión 2 creada: {sub2.mission_id} - {sub2.active_goal}")
    
    # 4. Establecer Dependencia: Sub2 depende de Sub1
    mission_manager.add_dependency(sub2.mission_id, sub1.mission_id)
    print(f"Dependencia establecida: SUB2 bloqueda por SUB1.")
    
    # Verificar bloqueo
    sub2_reloaded = mission_manager.get_mission_by_id(sub2.mission_id)
    print(f"Estado SUB2: {sub2_reloaded.status} (Esperado: BLOCKED)")
    print(f"Razones de bloqueo: {sub2_reloaded.blocked_reasons}")
    
    # 5. Completar Sub1
    print("\n--- Completando SUB1 explicítamente... ---")
    # Para completar una misión necesitamos que sea la activa o llamar a set_status directamente
    # En un flujo real sería close_current_mission si es la activa.
    sub1.status = MissionStatus.COMPLETED
    mission_manager.save_mission(sub1)
    
    # Disparar re-evaluación (normalmente se dispara al cerrar/completar en el flujo real)
    mission_manager.reevaluate_dependents(sub1.mission_id)
    
    # 6. Verificar desbloqueo de Sub2
    sub2_final = mission_manager.get_mission_by_id(sub2.mission_id)
    print(f"Estado SUB2 tras completar SUB1: {sub2_final.status} (Esperado: OPEN)")
    print(f"Razones de bloqueo remanentes: {sub2_final.blocked_reasons}")
    
    # 7. Verificar jerarquía del padre
    parent_final = mission_manager.get_mission_by_id(parent.mission_id)
    print(f"Hijos de la misión padre: {len(parent_final.child_ids)}")
    
    print("\n--- ✅ VALIDACIÓN DE JERARQUÍA COMPLETADA ---")

if __name__ == "__main__":
    asyncio.run(validate_hierarchy())
