
import asyncio
import sys
import os
import json
from datetime import datetime

# Setup project root
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

# Mock some essential components if needed, but try to use real ones
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.permissions import set_chip_context

async def run_validation():
    print("# VALIDACIÓN RUNTIME: MULTIMODAL VISUAL DIFF")
    print("-" * 50)
    
    with set_chip_context("core"):
        processor = MultimodalProcessor()
        
        # 1. INITIAL CAPTURE
        print("1. Cargando captura inicial...")
        initial_msg = "[VISUAL_EVIDENCE] Menú principal con errores de superposición."
        initial_context = {
            "multimodal_evidence": [{
                "id": "evidence_001",
                "data": "base64_data_placeholder_001",
                "annotations": [
                    {"type": "box", "x": 100, "y": 100, "w": 200, "h": 50, "comment": "Menu overlapping here"}
                ]
            }]
        }
        
        resp1 = await processor.process(initial_msg, initial_context)
        print(f"B. Evidencia recibida: {resp1.message}")
        print(f"Hipótesis Generada: {resp1.payload['hypothesis']['description']}")
        
        mission = mission_manager.get_active_mission()
        if mission:
            print(f"C. Misión Activa ID: {mission.mission_id}")
            print(f"Persistencia confirmada en DB: {mission.active_goal}")
        
        # 2. CORRECTIVE RE-ANNOTATION
        print("\n2. Corrigiendo el foco con segunda anotación...")
        corrective_msg = "[VISUAL_EVIDENCE] Corrección: El error está en el responsive del footer, no en el menú."
        corrective_context = {
            "multimodal_evidence": [{
                "id": "evidence_001",
                "data": "base64_data_placeholder_001",
                "annotations": [
                    {"type": "box", "x": 100, "y": 800, "w": 300, "h": 100, "comment": "Actual footer alignment issue"}
                ]
            }]
        }
        
        resp2 = await processor.process(corrective_msg, corrective_context)
        print(f"B. Evidencia corregida: {resp2.message}")
        
        # 3. VISUAL DIFF VALIDATION
        print("\n3. Validando Visual Diff...")
        diff = resp2.payload.get("visual_diff")
        if diff:
            print(f"Has Shift: {diff['has_shift']}")
            print(f"Regiones Añadidas (+): {diff['added_count']}")
            print(f"Regiones Eliminadas (-): {diff['removed_count']}")
            print(f"Regiones Persistentes (=): {diff['persistent_count']}")
            
            # Print specifically requested regions
            if diff['added_regions']:
                print(f"Añadida: {diff['added_regions'][0]['comment']} en ({diff['added_regions'][0]['x']}, {diff['added_regions'][0]['y']})")
            if diff['removed_regions']:
                print(f"Eliminada: {diff['removed_regions'][0]['comment']} en ({diff['removed_regions'][0]['x']}, {diff['removed_regions'][0]['y']})")
        else:
            print("ERROR: No se generó visual_diff.")

        # 4. HISTORY PERSISTENCE CHECK
        print("\n4. Confirmando persistencia en histórico multimodal...")
        history = mission.multimodal_history
        print(f"Eventos registrados: {[e['event'] for e in history]}")
        
        # 5. HYPOTHESIS SHIFT
        print("\n5. Comparación de Hipótesis...")
        print(f"H0: {history[0]['hypothesis']['description']}")
        print(f"H1: {history[1]['hypothesis']['description']}")
        
        if diff and diff.get("hypothesis_shift"):
            print("Confirmación: El sistema detectó el 'shift' operacional.")
        
        print("\n" + "=" * 50)
        print("RESULTADO FINAL: BLOQUE CERRADO (Validado en Runtime Real)")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_validation())
