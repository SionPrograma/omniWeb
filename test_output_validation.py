import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.auth import OmniUser

async def test_prompts():
    user = OmniUser(id="test_user", username="tester", email="test@omni.web", role="admin")
    context = {"user_id": user.id, "username": user.username, "multimodal_evidence": []}
    
    prompts = [
        ("HOLA", "hola"),
        ("CHISTE", "contame un chiste"),
        ("ESTADO", "estado"),
        ("ORDEN TÉCNICA", "auditá sistema")
    ]
    
    print("--- INICIANDO VALIDACIÓN DE VOZ ÚNICA (SILENT DIRECTOR) ---")
    
    for label, prompt in prompts:
        print(f"\nPROBANDO: [{label}] -> '{prompt}'")
        try:
            res = await ai_command_router.route(prompt, context=context)
            msg = res.message
            
            print(f"OUTPUT: \"{msg[:100]}...\"" if len(msg) > 100 else f"OUTPUT: \"{msg}\"")
            
            # Check for contamination
            contaminators = [
                "ANÁLISIS COGNITIVO", 
                "MISIÓN DISPUESTA", 
                "TECHNICAL HYPOTHESIS", 
                "INFORME DE AUDITORÍA",
                "POLÍTICA OPERATIVA",
                "Para mí que el tema viene por",
                "Me voy a centrar en que",
                "Chequeá",
                "\"intent\":", # JSON leaks
                "\"status\":"
            ]
            
            leaks = [c for c in contaminators if c.lower() in msg.lower()]
            if leaks:
                print(f"❌ FALLO: Contaminación detectada: {leaks}")
            else:
                print("✅ LIMPIO: Sin voces duplicadas ni headers internos.")
                
            # Specific checks
            if label == "ESTADO" and ("{" in msg or "[" in msg):
                print("❌ FALLO: Posible leak de JSON en reporte de estado.")
                
        except Exception as e:
            print(f"⚠️ ERROR AL PROCESAR: {e}")

    print("\n--- FIN DE VALIDACIÓN ---")

if __name__ == "__main__":
    asyncio.run(test_prompts())
