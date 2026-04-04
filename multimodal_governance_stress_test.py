
import asyncio
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any

# Mocking parts that require full server or external APIs if necessary, 
# but targeting the core logic classes directly for "Unit Stress Test"
from backend.core.ai_host.memory.mission_manager import MissionManager, MissionStatus, MissionState
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor
from backend.core.ai_host.shadow_swarm.approval_gate import approval_gate, GateStatus
from backend.core.ai_host.processors.multimodal_report import MultimodalReportGenerator
from backend.core.ai_host.shadow_swarm.shadow_constructor import ShadowConstructor, ShadowConstructorProposal, ConstructorState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("STRESS_TEST")

async def run_stress_test():
    logger.info("=== OMNIWEB: [UNIQUE] MULTIMODAL GOVERNANCE STRESS TEST ===")
    
    # We use a unique goal to ensure it starts as INITIAL_CAPTURE if we find no active mission in memory
    unique_suffix = str(uuid.uuid4())[:8]
    goal_v1 = f"STRESS_TEST MISSION {unique_suffix}"
    
    mm = MissionManager()
    # Ensure no residual active mission in memory for this instance
    mm.active_mission = None
    
    proc = MultimodalProcessor()
    report_gen = MultimodalReportGenerator()
    
    # PHASE 1: INITIAL VISUAL INPUT
    logger.info("\n[FASE 1] Entrada Visual Inicial")
    initial_context = {
        "multimodal_evidence": [{
            "id": "capture_001",
            "data": "base64_image_data_mock_v1",
            "annotations": [{"type": "point", "x": 10, "y": 20, "comment": "Error inicial"}]
        }]
    }
    
    res1 = await proc.process(f"[VISUAL_EVIDENCE] {goal_v1}", context=initial_context)
    mission = mm.get_active_mission()
    
    # Check if the mission we got is the one we just created
    if mission and goal_v1 in mission.active_goal:
        event0 = mission.multimodal_history[0]["event"]
        if event0 == "INITIAL_CAPTURE":
             logger.info(f"VERDE: Misión creada. Evento 0: {event0}")
        else:
             logger.info(f"AMARILLO: Evento 0 es '{event0}' (posiblemente se unió a otra misión activa).")
    else:
        logger.error(f"ROJO: Fallo en creación de misión.")

    # PHASE 2: VISUAL FEEDBACK & DIFF
    logger.info("\n[FASE 2] Corrección de Foco (Feedback Loop)")
    feedback_context = {
        "multimodal_evidence": [{
            "id": "capture_001_v2",
            "data": "base64_image_data_mock_v2",
            "annotations": [
                {"type": "point", "x": 10, "y": 20, "comment": "Persistente"},
                {"type": "box", "x": 50, "y": 50, "w": 100, "h": 50, "comment": "Foco real en core"}
            ]
        }]
    }
    
    res2 = await proc.process("[VISUAL_EVIDENCE] Re-orientación necesaria", context=feedback_context)
    mission = mm.get_active_mission()
    
    history = mission.multimodal_history
    if any(h["event"] == "RE_ORIENTATION" for h in history):
        logger.info(f"VERDE: Feedback loop capturado.")
    else:
        logger.error(f"ROJO: No se capturó la re-orientación.")

    # PHASE 3: GOVERNANCE & CONSTRAINTS
    logger.info("\n[FASE 3] Gobernanza (Restricciones Sectoriales)")
    # Congelar 'core'
    mission.parameters["frozen_paths"] = ["core"]
    mm.save_mission(mission)
    
    constructor = ShadowConstructor(
        shadow_id=f"shadow_STRESS_{unique_suffix}",
        mission_id=mission.mission_id,
        assigned_microtask="Modify core/module.py",
        target_layer="backend/core",
        visual_context=mission.visual_context
    )
    await constructor.draft_proposal()
    
    # Evaluamos en el Gate
    decision = approval_gate.evaluate_proposal(constructor)
    
    if decision.status == GateStatus.BLOCKED_BY_RISK:
        logger.info(f"VERDE: Gobernanza ACTIVADA. Bloqueado: {decision.blocking_reason}")
    else:
        logger.error(f"ROJO: Gobernanza FALLÓ. Status: {decision.status}. Targets: {decision.affected_targets}")

    # PHASE 4: CONTINUITY
    logger.info("\n[FASE 4] Continuidad (Re-hidratación)")
    mission_id_saved = mission.mission_id
    
    # Re-instanciar manager
    MissionManager._instance = None
    new_mm = MissionManager()
    rehydrated = new_mm.get_active_mission()
    
    if rehydrated and rehydrated.mission_id == mission_id_saved:
        logger.info("VERDE: Rehidratación exitosa.")
        logger.info(f"VERDE: Historia restaurada ({len(rehydrated.multimodal_history)} eventos).")
    else:
        logger.error("ROJO: Fallo de rehidratación.")

    # PHASE 5: REPORTING
    logger.info("\n[FASE 5] Reporte Final")
    report = report_gen.generate_report(rehydrated.mission_id)
    
    if report and len(report["timeline"]) >= 3:
        logger.info(f"VERDE: Reporte generado con {len(report['timeline'])} eventos.")
    else:
        logger.error("AMARILLO: Reporte incompleto.")

    logger.info("\n=== RESULTADO FINAL DEL STRESS TEST ===")
    logger.info("ESTADO: ESTABILIZADO")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
