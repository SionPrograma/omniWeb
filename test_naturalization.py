
import re

class MockResponse:
    def __init__(self, message):
        self.message = message

def _naturalize(text: str) -> str:
    import re
    
    # 1. Strip All Emojis and mechanical markers
    text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]', '', text)
    
    # 2. Aggressive Label & Marker Removal
    labels = [
        "OBSERVATION", "OBSERVACIÓN", "ANALYSIS", "ANÁLISIS", "PLAN", "MISSION", "MISIÓN",
        "HYPOTHESIS PRIMARIA", "HIPÓTESIS PRIMARIA", "HYPOTHESIS", "HIPÓTESIS",
        "ALTERNATIVE EXPLANATION", "EXPLICACIÓN ALTERNATIVA", "EVIDENCE", "EVIDENCIA",
        "CONFIDENCE LEVEL", "NIVEL DE CONFIANZA", "MISSING EVIDENCE", "EVIDENCIA FALTANTE",
        "RECOMMENDED ACTION", "ACCIÓN RECOMENDADA", "RECOMMENDED NEXT STEP",
        "RELIABILITY", "CONFIABILIDAD", "LEARNING", "APRENDIZAJE", "PATCH", "PARCHE", 
        "CONTEXTO COGNITIVO", "TECHNICAL REASONING", "SYSTEM STATUS", "PRIMARIA", "SECUNDARIA",
        "TO", "FROM", "ORIGINAL", "TRANSLATED", "CONFIRMATION", "YOUR CONTACTS", "CONTACTS",
        "MESSAGE", "ORIGINAL TEXT", "TARGET LANGUAGE", "STATUS", "RECIPIENT"
    ]
    
    label_pattern = "|".join(sorted(labels, key=len, reverse=True)) 
    forbidden_regex = rf'(?i)^\s*([\*\#\-\s\•\d\.\)]*)*({label_pattern})[\*\#\s]*[:\s\-]*'
    
    # Strip Markdown formatting
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\_\_(.*?)\_\_', r'\1', text)
    
    # Apply the line-by-line transformation
    raw_lines = text.split('\n')
    processed_sentences = []
    
    for line in raw_lines:
        line = line.strip()
        if not line: continue
        
        # Strip the specific forbidden patterns at start of line
        clean_line = re.sub(forbidden_regex, '', line)
        
        # Strip remaining list markers
        clean_line = re.sub(r'^[\-\*\•]\s*', '', clean_line)
        clean_line = re.sub(r'^\d+[\.\)]\s*', '', clean_line)
        
        # Strip leading/trailing punctuation artifacts
        clean_line = clean_line.strip(' :-•·')
        
        if clean_line:
            # Ensure sentence casing
            if len(clean_line) > 1:
                clean_line = clean_line[0].upper() + clean_line[1:]
            
            # Ensure sentence ending
            if not clean_line[-1] in ['.', '!', '?', ';']:
                clean_line += '.'
            
            processed_sentences.append(clean_line)
    
    if not processed_sentences:
        return "Entendido. He procesado la información y todo parece estar en orden."

    # 3. Join into a single flow
    unified_flow = " ".join(processed_sentences)
    
    # 4. Post-Process cleanup
    unified_flow = re.sub(r'\s*[\.\,]\s*[\.\,]', '.', unified_flow)
    unified_flow = re.sub(r'([\.!\?])\s*[\.\,]+', r'\1', unified_flow)
    unified_flow = re.sub(r'\.{2,}', '.', unified_flow)
    unified_flow = re.sub(r'\s{2,}', ' ', unified_flow)
    
    # Final sanity check
    unified_flow = unified_flow.strip().rstrip(' :-•')
    if unified_flow and not unified_flow[-1] in ['.', '!', '?']:
        unified_flow += '.'
        
    return unified_flow

# New test cases inclusive of communication and emojis
test_cases = [
    "OBSERVACIÓN: El sistema está nominal.",
    "HIPÓTESIS PRIMARIA: Error en base de datos.",
    "**ANÁLISIS**: Detecto latencia alta.",
    "1. PLAN: Reiniciar servicios.\n2. MISIÓN: Estabilizar núcleo.",
    "EXPLICACIÓN ALTERNATIVA: El usuario no tiene permisos.",
    "📨 **To**: Juan\n📝 **Original**: Hola\n🌐 **Translated**: Hi\nSend this?",
    "✅ Tarea completada con éxito 🚀",
    "CONTEXTO COGNITIVO: Memoria saturada."
]

print("--- TESTING NATURALIZATION LAYER ---")
for i, tc in enumerate(test_cases, 1):
    print(f"\nINPUT {i}: {tc}")
    print(f"OUTPUT {i}: {[_naturalize(tc)]}")

# TEST CASE: Compound labels
input_complex = """
**OBSERVACIÓN**: El servidor 8000 está ocupado.
**HIPÓTESIS PRIMARIA**: Podría ser el chip de finanzas.
**EXPLICACIÓN ALTERNATIVA**: Tal vez sea el chip de reparto.
**ACCIÓN RECOMENDADA**: Detener el servidor y reiniciar.
"""

print("\n--- BRAIN OUTPUT (COMPLEX) ---")
print(input_complex)
print("\n--- ORCHESTRATOR OUTPUT ---")
print(_naturalize(input_complex))
