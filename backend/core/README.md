# Backend Core (Python)

> **⚠️ AVISO ESTRUCTURAL IMPORTANTE:**
> No confundir este directorio reservado para el servidor (`backend/core/`) con la suite Javascript central (`core/` en la raíz).

Este directorio es responsable de orquestar la mecánica vital de FastAPI y la seguridad / descubrimiento de OmniWeb. Todo el código aquí debe estar escrito en Python.

## Archivos clave actuales (v0.2.0):
- `config.py`: Definición de perfiles `.env` y declaración de los `ACTIVE_MODULES` (`chips/` listados).
- `module_registry.py`: Motor lógico que monta automáticamente los frontends (`/frontend/...`) de `chips/` y asienta sus API Routers.
- `event_bus.py`: Canal de comunicación y observabilidad base p/módulos backend.
