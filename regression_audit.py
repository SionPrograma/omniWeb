import sys
import os
import re
from typing import Dict, Any

# Set project root to sys.path
root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(root)

from backend.core.ai_host.orchestration.executive_synthesis import ExecutiveSynthesis
from backend.core.ai_host.intent_understanding.human_input_interpreter import human_interpreter

es = ExecutiveSynthesis()

# Mock Populated Memories
working_populated = {
    "last_important_file": "backend/core/ai_host/orchestration/executive_synthesis.py",
    "last_operation_summary": "ajuste de lógica de fallback"
}
project_populated = {
    "roadmap_block": "Bloque 5", 
    "validated_fixes": ["Fix de redirección de ruteo", "Cierre de Bloque 4"], 
    "deferred_items": ["Memoria total de larga duración"], 
    "sensitive_modules": ["backend/core/ai_host/processors/proposal_processor.py"]
}

# Mock Empty Memories (to check fallbacks)
working_empty = {"last_important_file": None, "last_operation_summary": None}

def test_case(name, query, working, project):
    print(f"\n--- {name} ---")
    print(f"QUERY: {query}")
    
    # Simulate Human Input Interpretation (Self-correction)
    interpretation = human_interpreter.interpret(query)
    refined_query = interpretation.get("refined_text", query)
    if refined_query != query:
        print(f"REFINED: {refined_query}")
    
    # Synthesis
    result = es.synthesize(working, project, refined_query, lang="es")
    print(f"RESULTADO: {result}")
    return result

# CASO A: Working Memory Populated
test_case("CASO A", "¿Qué estábamos haciendo?", working_populated, project_populated)

# CASO B: Project Memory
test_case("CASO B", "¿En qué bloque estamos?", working_populated, project_populated)

# CASO C: Validated Fixes
test_case("CASO C", "¿Qué fixes ya están cerrados?", working_populated, project_populated)

# CASO D: Memory Composition
test_case("CASO D", "Vale, y eso que estábamos haciendo, ¿pertenece al bloque actual o me estoy mezclando de bloque?", working_populated, project_populated)

# CASO E: Mixed, Self-correction, Explicit instructions
q_e = "Omni, what were we doing before this y en qué bloque estamos, no, mejor dicho: decime solo qué parte sigue vigente ahora, qué fix ya sería redundant to reopen, y qué módulo sensible no debería tocar aunque parezca conectado con lo último."
test_case("CASO E", q_e, working_populated, project_populated)

# CASO E (Fallback): Same query but with EMPTY working memory
test_case("CASO E (EMPTY WORKING)", q_e, working_empty, project_populated)

# CASO F: Voice scenario (Simulated signals)
# We test keyword "sensible" and "proposal_processor" in query to ensure no deformation.
q_f = "Che, fijate si hay riesgo en tocar el modulo sensible de proposal_processor"
test_case("CASO F", q_f, working_populated, project_populated)
