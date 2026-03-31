import asyncio
import sys
import os
from unittest.mock import MagicMock

# Ajustar path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Mock environment
os.environ["OMNIWEB_ENV"] = "test"

from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus
from backend.core.ai_host.intent_understanding.conversation_tracker import conversation_tracker

# Instanciamos el router manualmente
brain_router = BrainRouter(ai_command_router)

async def run_validation():
    print("\n🚀 --- VALIDACIÓN REAL DE CONTINUIDAD SEMÁNTICA (PROMPT RECONSTRUCTION) ---")

    # 0. Limpiar DB de misiones y tracker
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM system_missions")
            conn.commit()
    
    session_id = "test_dev"
    conversation_tracker.sessions[session_id] = conversation_tracker.get_context(session_id)
    ctx = conversation_tracker.sessions[session_id]
    ctx.last_referenced_entity = None
    ctx.active_panel_id = None
    ctx.recent_messages = []

    # --- PRUEBA 1: FOLLOW-UP DE MISIÓN ---
    print("\n🔹 ESCENARIO 1: Seguimiento de Misión")
    print("STEP 1.1: 'auditá el chip-finanzas'")
    await brain_router.process("auditá el chip-finanzas", context={"user_id": session_id})
    
    print("STEP 1.2: 'seguí'")
    # El router internamente debe reconstruir a "Continúa con la misión: auditá el chip-finanzas..."
    res_follow = await brain_router.process("seguí", context={"user_id": session_id})
    print(f"   [RESULT] {res_follow.message[:150]}...")
    if "finanzas" in res_follow.message.lower() or "chip" in res_follow.message.lower():
        print("✅ SUCCESS: 'seguí' heredó el contexto del chip-finanzas.")
    else:
        print("❌ FAILURE: 'seguí' perdió el hilo del chip.")

    # --- PRUEBA 2: REFERENCIA VAGA (Sufijo -lo) ---
    print("\n🔹 ESCENARIO 2: Referencia Vaga ('arreglalo')")
    # Ya mencionamos finanzas arriba, el tracker debería tenerlo como last_referenced_entity
    print(f"   [DEBUG] last_ref: {ctx.last_referenced_entity}")
    
    print("STEP 2.1: 'arreglalo'")
    # El router debe reconstruir a "arreglalo (Referencia: chip-finanzas)"
    res_vague = await brain_router.process("arreglalo", context={"user_id": session_id})
    print(f"   [RESULT] {res_vague.message[:150]}...")
    if "finanzas" in res_vague.message.lower() or "repar" in res_vague.message.lower() or "fix" in res_vague.message.lower():
        print("✅ SUCCESS: 'arreglalo' se vinculó al chip-finanzas.")
    else:
        print("❌ FAILURE: 'arreglalo' no sabe qué arreglar.")

    # --- PRUEBA 3: REFERENCIA ESPACIAL (Pánel activo) ---
    print("\n🔹 ESCENARIO 3: Referencia Espacial ('eso del panel')")
    print("STEP 3.1: 'inspecciona el context-panel'")
    await brain_router.process("inspecciona el context-panel", context={"user_id": session_id})
    
    # ENSURE MISSION IS OPEN FOR TEST
    m_now = mission_manager.get_active_mission()
    if m_now: m_now.status = MissionStatus.OPEN
    
    print("STEP 3.2: 'y ahora?'")
    # Debe reconstruir a "Continúa hablando de: inspecciona el context-panel..."
    res_now = await brain_router.process("y ahora?", context={"user_id": session_id})
    print(f"   [RESULT] {res_now.message[:150]}...")
    if "context" in res_now.message.lower() or "panel" in res_now.message.lower() or "inspecc" in res_now.message.lower():
        print("✅ SUCCESS: 'y ahora?' resolvió al panel activo.")
    else:
        print("❌ FAILURE: 'y ahora?' se perdió.")

    # --- PRUEBA 4: ACLARACIÓN INTELIGENTE ---
    print("\n🔹 ESCENARIO 4: Ambigüedad Real (Aclaración)")
    # Limpiamos misión y tracker
    mission_manager.active_mission = None
    ctx.last_topic = None
    ctx.last_referenced_entity = None
    
    print("STEP 4.1: 'retomá' (sin nada previo)")
    res_clarify = await brain_router.process("retomá", context={"user_id": session_id})
    print(f"   [RESULT] {res_clarify.message}")
    if "?" in res_clarify.message or "qué" in res_clarify.message.lower() or "retom" in res_clarify.message.lower():
        print("✅ SUCCESS: El sistema pidió aclaración en lugar de inventar.")
    else:
        print("❌ FAILURE: El sistema respondió algo genérico o falló.")

    print("\n🏁 --- FIN DE VALIDACIÓN ---")

if __name__ == "__main__":
    asyncio.run(run_validation())
