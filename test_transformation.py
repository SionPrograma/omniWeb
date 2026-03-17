
import re

def _transform_to_natural_language(text: str) -> str:
    # 1. Remove markers like **HEADER** or ### HEADER
    text = re.sub(r'\*\*.*?\*\*', '', text) # Remove all bold markers
    text = re.sub(r'#+\s+.*?\n', '\n', text) # Remove headers
    
    # 2. Specific label removal
    forbidden_labels = [
        "OBSERVATION", "OBSERVACIÓN", "ANALYSIS", "ANÁLISIS",
        "HYPOTHESIS", "HIPÓTESIS", "PLAN", "MISSION", "MISIÓN",
        "EVIDENCE", "EVIDENCIA", "RELIABILITY", "CONFIABILIDAD",
        "LEARNING", "APRENDIZAJE", "PATCH", "PARCHE", "CONTEXTO COGNITIVO"
    ]
    for label in forbidden_labels:
        text = re.sub(rf'(?i){label}[:\s]*', '', text)

    # 3. Remove list markers
    text = re.sub(r'^[\-\*\•]\s*', '', text, flags=re.MULTILINE)
    
    # 4. Clean up whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # 5. Join into a single flow
    # If a line ends with a period/question/exclamation, just join.
    # Otherwise add a period.
    result = ""
    for line in lines:
        if result:
            if not result.endswith(('.', '!', '?', ':')):
                result += ". "
            else:
                result += " "
        result += line
        
    return result

# TEST
input_text = """
**OBSERVATION**
El sistema está funcionando correctamente.

**ANALYSIS**
He detectado que la latencia es de 50ms.

**PLAN**
1. Seguir monitoreando.
2. Notificar al usuario.

**CONTEXTO COGNITIVO**
- Contexto reciente: hola
"""

print("--- BEFORE ---")
print(input_text)
print("--- AFTER ---")
print(_transform_to_natural_language(input_text))
