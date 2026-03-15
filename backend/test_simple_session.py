from backend.core.ai_host.sessions import session_state

print("Initial Language:", session_state.language)
session_state.set_language("responde en inglés")
print("New Language:", session_state.language)
session_state.set_language("speak in spanish")
print("New Language:", session_state.language)
