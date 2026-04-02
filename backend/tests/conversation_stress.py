import asyncio
import logging
from backend.core.ai_host.routing.command_router import CommandRouter

async def test_conversation():
    router = CommandRouter()
    
    test_cases = [
        ("Hola, quien sos?", "identity"),
        ("Me siento un poco perdido hoy.", "chat"),
        ("Por que?", "followup"),
        ("Pero, ¿podes ayudarme con algo técnico si te lo pido?", "chat"),
        ("seguí", "mission_followup"),
    ]
    
    print("\n" + "="*50)
    print("AUDITORÍA CONVERSACIONAL - ESTRÉS")
    print("="*50)
    
    for msg, expected in test_cases:
        print(f"\n[USER]: {msg}")
        # Simulamos contexto de Chat Shell Público
        ctx = {"source_surface": "chat", "user_id": "test_user"}
        res = await router.route(msg, context=ctx)
        print(f"[OMNI (Intent: {res.intent})]: {res.message}")
        
        # Clasificación heurística
        if "No detecté un comando operativo" in res.message or "Tal vez me puse un poco rígido" in res.message:
            print(">>> [ROJO] Fallback estático detectado.")
        else:
            print(">>> [VERDE/AMARILLO] Respuesta dinámica.")

if __name__ == "__main__":
    asyncio.run(test_conversation())
