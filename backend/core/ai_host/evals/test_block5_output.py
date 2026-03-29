
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.ai_host.processors.base import AICommandResponse
from backend.core.permissions import set_chip_context

async def test_output_consistency():
    orchestrator = CognitiveOrchestrator()
    
    # MOCK CREATOR CONTEXT
    with set_chip_context("core", user_id="1"):
        
        # 1. TEST CASE: Proposal (Regular)
        print("--- CASE 1: PROPOSAL (Humanized) ---")
        raw_proposal = """ARCHIVO_LEIDO: backend/core/ai_host/orchestration/cognitive_orchestrator.py
RESUMEN_REAL: Módulo de orquestación.
MICROFIX_PROPUESTO: Añadir tipos.
IMPACTO_RELACIONADO: MEDIO
CRITERIO_DE_SEGURIDAD: CAMBIO_SEGURO
---
- diff line
+ diff line"""
        
        res1 = await orchestrator.orchestrate(
            message="analizá",
            understanding={"mode": "reflective_analysis", "intent_group": "COPILOT_PROPOSAL_INTENT"},
            context={"user_id": "1"},
            raw_response=AICommandResponse(intent="copilot_proposal", status="success", message=raw_proposal)
        )
        print(res1.message[:200] + "...")
        assert "PROPUESTA DE MEJORA" in res1.message
        assert "**Hallazgo:**" in res1.message
        
        # 2. TEST CASE: Audit (No Changes)
        print("\n--- CASE 2: AUDIT ONLY (No Changes) ---")
        raw_audit = """SCOPE_RAÍZ: backend/core/ai_host
ARCHIVOS_RELEVANTES: coordinator.py, engine.py
CAMBIO_PROPUESTO_POR_ARCHIVO: Ninguno estructural. Auditoría nominal completa.
IMPACTO_RELACIONADO: NULO
CRITERIO_DE_SEGURIDAD: CAMBIO_SEGURO"""
        
        res2 = await orchestrator.orchestrate(
            message="auditá core",
            understanding={"mode": "reflective_analysis", "intent_group": "SYSTEM_AUDIT_INTENT"},
            context={"user_id": "1"},
            raw_response=AICommandResponse(intent="copilot_proposal", status="success", message=raw_audit)
        )
        print(res2.message[:200] + "...")
        assert "INFORME DE AUDITORÍA TÉCNICA" in res2.message
        assert "**Seguridad y Riesgo:**" in res2.message
        
        # 3. TEST CASE: High Risk Alert
        print("\n--- CASE 3: HIGH RISK (Alert Injected) ---")
        raw_risk = """ARCHIVO_LEIDO: backend/core/security/manager.py
RESUMEN_REAL: Módulo crítico de acceso.
MICROFIX_PROPUESTO: Cambiar salt.
IMPACTO_RELACIONADO: ALTO: CORE ACCESS CONTROL
CRITERIO_DE_SEGURIDAD: CAMBIO_RIESGO_MEDIO_CORE"""
        
        res3 = await orchestrator.orchestrate(
            message="analizá seguridad",
            understanding={"mode": "reflective_analysis", "intent_group": "COPILOT_PROPOSAL_INTENT"},
            context={"user_id": "1"},
            raw_response=AICommandResponse(intent="copilot_proposal", status="success", message=raw_risk)
        )
        print(res3.message)
        assert "[!IMPORTANT]" in res3.message
        
        # 4. TEST CASE: CONSTRAINED (SOLO)
        print("\n--- CASE 4: CONSTRAINED (SOLO) ---")
        res4 = await orchestrator.orchestrate(
            message="SOLO archivo_leido",
            understanding={"mode": "constrained_output", "intent_group": "COPILOT_PROPOSAL_INTENT"},
            context={"user_id": "1"},
            raw_response=AICommandResponse(intent="copilot_proposal", status="success", message=raw_proposal)
        )
        print(res4.message)
        assert "ARCHIVO_LEIDO:" in res4.message
        assert "PROPUESTA" not in res4.message

    print("\n[OK] All consistency tests passed (Structural integrity verified).")

if __name__ == "__main__":
    asyncio.run(test_output_consistency())
