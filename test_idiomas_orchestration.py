import asyncio
import sys

async def validate():
    print("OmniWeb - Local Sovereign Orchestrator Valiation for Chip-Idiomas")
    
    

    prompts = [
        {"desc": "Greeting", "text": "Hola, Omni"},
        {"desc": "Translation", "text": "Traduce 'OmniWeb is scaling so fast'"},
        {"desc": "Spanglish", "text": "Hola, my friend, english and español bien"},
        {"desc": "Summary", "text": "Resumen de lo que estamos haciendo"},
        {"desc": "Correction", "text": "Corrige esta frase mal escrita"},
        {"desc": "Explanation", "text": "explica omni"},
        {"desc": "Short mode", "text": "corto: ¿omniweb?"},
        {"desc": "Detailed mode", "text": "explica en detalle si?"},
        {"desc": "Organic catch-all", "text": "Hablame de cualquier cosa"}
    ]
    
    print("\n--- Testing Direct Engine Routing ---")
    # This validates the internal structure is perfectly wired without full uvicorn

    for p in prompts:
        print(f"\n[Scenario: {p['desc']}]")
        print(f"Request: {p['text']}")
        try:
            # We must import from the correct path since the folder is chip-idiomas (hyphen):
            import importlib
            mod = importlib.import_module("chips.chip-idiomas.core.services.language_engine")
            res = await mod.language_engine.enhance_natural_chat(p['text'], {}, "es")
            print(f"Engine Response: {res}")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(validate())
