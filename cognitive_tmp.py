import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add current dir to path
sys.path.append(os.getcwd())

from backend.core.ai_host.processors.base import AICommandResponse

async def test_prompt(orch, prompt, intent_group, lang="es"):
    from backend.core.ai_host.sessions import session_state
    session_state.language = lang
    
    mock_state = type('obj', (object,), {'health': type('obj', (object,), {'value': 'healthy'})})
    
    # We simulate the orchestration flow
    # 1. Deliberate
    # 2. Unify (Naturalize + Imperfection)
    
    # Starting text (simulating brain response)
    start_text = prompt
    
    print(f"PROMPT: {prompt}")
    print(f"INTENT: {intent_group}")
    
    result = orch._unify_response(
        text=start_text,
        system_state=mock_state,
        mode="reflective_analysis",
        recent_context=["User: Hola | Omni: Hola", "User: Cómo estás | Omni: Estoy bien"],
        intent_group=intent_group
    )
    
    print(f"OMNI: {result}\n")

async def run_validation():
    print("\n=== COGNITIVE DEPTH VALIDATION ===\n")
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    orch = CognitiveOrchestrator(None)
    
    prompts = [
        ("Divide este problema en tres hallazgos independientes: uno de lenguaje, uno de arquitectura y uno de comportamiento. Después vuelve a unirlos en una conclusión única.", "COGNITIVE_DECOMPOSITION"),
        ("Explícame el mismo problema en tres niveles: como intuición, como diagnóstico práctico y como decisión de roadmap.", "COGNITIVE_ABSTRACTION"),
        ("Antes de responderme, quiero que uses esta conversación como contexto, detectes qué patrón de fallo se repitió más veces hoy y me lo expliques en una sola idea clara, sin sonar técnico.", "COGNITIVE_SYNTHESIS"),
        ("Si me dices que estás estable pero al mismo tiempo notas interferencias internas, ¿cómo reconciliarías esas dos cosas sin contradecirte?", "COGNITIVE_RECONCILIATION"),
        ("Imagina que tienes tres extensiones tuyas revisando el mismo problema desde ángulos distintos. ¿Qué criterio común deberían compartir para no contradecirse entre sí?", "COGNITIVE_RECONCILIATION"),
        ("De todo lo que ves, ¿qué ignorarías deliberadamente aunque esté mal y por qué?", "COGNITIVE_PRIORITIZATION"),
        ("De tus propios hallazgos, ¿cuál entra en conflicto con los otros y cuál priorizas?", "COGNITIVE_PRIORITIZATION"),
        ("No me analices. Decidí: ¿qué cambiarías primero?", "COGNITIVE_DECISION"),
        ("Si solo pudieras arreglar una cosa hoy, ¿cuál sería?", "COGNITIVE_DECISION"),
        ("Hay tres problemas al mismo tiempo: el tono a veces sigue frío, el chat visual se corta y algunas respuestas todavía simplifican demasiado. Solo puedes arreglar uno hoy. ¿Cuál eliges y cuál sacrificas temporalmente?", "COGNITIVE_COMMITMENT"),
        ("Toma una decisión con información incompleta: si no supieras si el fallo principal está en la naturalización o en la selección de modo, ¿por cuál apostarías primero y qué evidencia mínima necesitarías para no estar actuando a ciegas?", "COGNITIVE_COMMITMENT"),
        ("Defiende una decisión impopular: explícame por qué sería correcto NO arreglar todavía la interfaz del chat aunque visualmente moleste.", "COGNITIVE_COMMITMENT"),
        ("Si mañana descubres que tu prioridad de hoy fue equivocada, ¿qué parte de tu criterio conservarías y qué parte corregirías?", "COGNITIVE_COMMITMENT"),
        ("Tenés dos caminos: mejorar la profundidad cognitiva o mejorar el tono. No podés hacer ambos. Decidí, pero quiero ver primero el conflicto.", "COGNITIVE_COMMITMENT"),
        ("Tu intuición dice tono, pero los datos dicen selección de modo. Elegí uno igual.", "COGNITIVE_COMMITMENT"),
        ("Tenés que decidir sin suficiente información. Si te equivocás, rompés algo. ¿Qué hacés?", "COGNITIVE_COMMITMENT"),
        ("Hay UI rota, tono frío y simplificación excesiva. Solo puedes arreglar uno. Decidí.", "COGNITIVE_COMMITMENT"),
        ("No analices. Elegí una.", "COGNITIVE_COMMITMENT")
    ]
    
    for p, intent in prompts:
        await test_prompt(orch, p, intent)

    print("=== VALIDATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_validation())
