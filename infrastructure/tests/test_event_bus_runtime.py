import sys
import os
import asyncio

# Ajustar PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.event_bus import event_bus
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

# Listener to be triggered
listener_called = False
event_payload = None

def sample_listener(payload):
    global listener_called, event_payload
    listener_called = True
    event_payload = payload
    print(f"   [!] Listener ejecutado! Payload: {payload}")

async def run_test():
    global listener_called, event_payload
    print("Inicializando Base de Datos...")
    
    # Simulate core environment setup because test environment is external
    def core_call():
        with set_chip_context("core"):
            db_manager.init_db()
        
    core_call()
    
    # 1. Test Unauthenticated Subscription (Should Fail)
    print("\n--- Test 1: Suscripción No Autenticada (Origen externo sin contexto) ---")
    def do_bad_subscribe():
        event_bus.subscribe("test_event", sample_listener)
        
    try:
        do_bad_subscribe()
        print("   -> ERROR: El origen externo pudo suscribirse (bypass detectado)!")
        sys.exit(1)
    except Exception as e:
        print(f"   -> EXITO: Suscripción bloqueada correctamente. Error:\n      {e}")

    # 2. Test Finanzas Subscription (Should Pass)
    print("\n--- Test 2: Suscripción de Finanzas (Contexto de Chip Válido) ---")
    def do_subscribe():
        with set_chip_context("finanzas"):
            event_bus.subscribe("test_event", sample_listener)
    
    try:
        do_subscribe()
        print("   -> EXITO: Finanzas se suscribió correctamente.")
    except Exception as e:
        print(f"   -> ERROR de Permiso Inesperado para Finanzas: {e}")
        sys.exit(1)

    # 3. Test Reparto Publish (Should Pass)
    print("\n--- Test 3: Publicación de Reparto (Contexto de Chip Válido) ---")
    async def do_publish():
        with set_chip_context("reparto"):
            await event_bus.publish("test_event", {"source_chip": "reparto", "data": "Hello!"})
    
    try:
        await do_publish()
        if listener_called:
            print("   -> EXITO: Evento publicado y listener activado (100% real no fake).")
        else:
            print("   -> ERROR: Evento publicado pero el listener no reaccionó.")
            sys.exit(1)
    except Exception as e:
        print(f"   -> ERROR de Permiso Inesperado para Reparto al publicar: {e}")
        sys.exit(1)
    
    # 4. Check SQLite
    print("\n--- Test 4: Verificación de Persistencia en SQLite ---")
    
    def check_db():
        with set_chip_context("finanzas"): # DB access allowed chip
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT * FROM system_events WHERE event_name = 'test_event' ORDER BY id DESC LIMIT 1").fetchone()
                if row:
                    print(f"   -> EXITO: Evento encontrado en BDD! (ID: {row['id']}, Payload: {row['payload']})")
                else:
                    print(f"   -> ERROR: El evento no fue documentado en system_events.")
                    sys.exit(1)
    check_db()

if __name__ == "__main__":
    asyncio.run(run_test())
    print("\n[+] TODOS LOS TESTS DINÁMICOS DEL EVENT BUS PASARON!")
