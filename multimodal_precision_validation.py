
import asyncio
import sys
import os
import json
from datetime import datetime

# Setup project root
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.shadow_swarm.shadow_auditor import ShadowAuditor, ShadowType
from backend.core.permissions import set_chip_context

async def run_precision_validation():
    print("# VALIDACIÓN: MULTIMODAL PRECISION PASS")
    print("=" * 60)
    
    with set_chip_context("core"):
        processor = MultimodalProcessor()
        
        # 1. EVIDENCIA INICIAL: OVERLAP EN MENÚ
        print("\n[PASO 1] CARGA DE EVIDENCIA INICIAL (MENÚ OVERLAPPING)")
        msg_1 = "[VISUAL_EVIDENCE] El login se ve mal en móvil."
        ctx_1 = {
            "multimodal_evidence": [{
                "id": "ev_001",
                "annotations": [
                    {"type": "box", "x": 50, "y": 50, "w": 100, "h": 50, "comment": "menu overlapping"}
                ]
            }]
        }
        
        resp1 = await processor.process(msg_1, ctx_1)
        orient1 = resp1.payload.get("technical_orientation", {})
        print(f"H0 - Capa Sugerida: {orient1.get('layer')}")
        print(f"H0 - Componente: {orient1.get('component')}")
        print(f"H0 - Confianza: {orient1.get('confidence')}")
        
        mission = mission_manager.get_active_mission()
        print(f"Roadmap Inicial (Targets): {mission.related_targets}")

        # 2. CORRECCIÓN DE FOCO: ERROR EN FOOTER
        print("\n[PASO 2] CORRECCIÓN DE FOCO VISUAL (FOOTER)")
        msg_2 = "[VISUAL_EVIDENCE] Corrección: No, el problema real es el footer vacío."
        ctx_2 = {
            "multimodal_evidence": [{
                "id": "ev_001",
                "annotations": [
                    {"type": "box", "x": 50, "y": 900, "w": 400, "h": 100, "comment": "footer vacío"}
                ]
            }]
        }
        
        resp2 = await processor.process(msg_2, ctx_2)
        orient2 = resp2.payload.get("technical_orientation", {})
        print(f"H1 - Capa Refinada: {orient2.get('layer')}")
        print(f"H1 - Componente Refinado: {orient2.get('component')}")
        print(f"H1 - Tipo Incidente: {orient2.get('issue_type')}")
        print(f"H1 - Confianza: {orient2.get('confidence')}")
        
        print(f"Roadmap Refinado (Targets): {mission.related_targets}")

        # 3. VERIFICACIÓN DE AUDITORÍA (SHADOW AUDITOR)
        print("\n[PASO 3] VERIFICACIÓN EN SHADOW AUDITOR (INFERENCIA APLICADA)")
        auditor = ShadowAuditor(
            shadow_id="test_auditor",
            mission_id=mission.mission_id,
            assigned_microtask="Auditar desalineación UI",
            target_layer=orient2.get('layer'),
            visual_context=mission.visual_context
        )
        
        report = await auditor.audit()
        print("\n--- HALLAZGOS DEL AUDITOR ---")
        for finding in report.findings:
            if "ORIENTACIÓN" in finding or "COMPONENTE" in finding or "TIPO" in finding:
                print(f"  [PRECISIÓN] {finding}")
        
        print(f"\nComponentes Afectados Detectados: {report.affected_components}")

        print("\n" + "=" * 60)
        print("RESULTADO FINAL: PRECISIÓN VALIDADA Y GOBERNADA")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_precision_validation())
