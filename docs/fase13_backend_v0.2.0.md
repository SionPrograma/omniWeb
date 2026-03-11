# Arquitectura de Backend v0.2.0: Orquestación y Dominios
ADR: Fase 4 - Consolidación del Servidor incremental

## 1. Diagnóstico del Backend Actual
En OmniWeb v0.2.0 el servidor base Python/FastAPI no opera como un monolito acoplado donde las rutas controlan el HTML con plantillas servidoras (Jinja). Funciona puramente como un **Orquestador MPA (Multi-Page App) y Servidor Estático Dinámico**. 
El bucle principal de la aplicación (`backend/main.py`) lee un archivo de configuración e inyecta dinámicamente:
1. Los recursos base compartidos (`/core`).
2. El portal visual del ecosistema (`/` -> `frontend/dashboard/index.html`).
3. Los sub-ecosistemas frontend de cada chip en su ruta propia (ej: `/finanzas`, `/reparto`).
4. (Punto de anclaje): Sus correspondientes API Routers en `/api/v1/{chip}`.

## 2. Identificación de Dominios y Responsabilidades Reales
El repositorio fragmenta inteligentemente la carga del backend en tres niveles innegociables:

1. **El Orquestador (`backend/main.py`)**
   - **Qué hace:** Levanta CORS, levanta `uvicorn`, expone un _Health Check_, y enruta carpetas a URLS.
   - **Qué NO hace:** No detalla lógica de negocios ("cómo guardar un ahorro"). No importa bases de datos de chips específicos.

2. **El Núcleo Python (`backend/core/`)**
   - **Qué hace:** Resguarda la meta-configuración (`config.py` con sus variables de entorno). Ofrece el motor lógico de emparejamiento API (`module_registry.py`) para evitar reescribir `main.py` cada vez que nace un nuevo chip. Aloja el bus interno de procesos (`event_bus.py`).
   - **Qué NO hace:** No provee código de interfaz visual.

3. **Las Tripas de Negocio Legacy (`modules/`)**
   - **Qué hace:** Alberga microservicios complejos que todavía no encajan visualmente en chips (ej. inferencia Whisper, modelos de Pydantic complejos, llamadas a APIs externas de IA).
   - **Qué NO hace:** Ya no alberga la UI de OmniWeb.

## 3. Relación actual entre Backend y Chips
Actualmente, los Chips modernos (`chip-reparto`, `chip-finanzas`, etc.) solicitan a FastAPI únicamente acceso al servidor web (para que HTML/CSS/JS sean despachados desde sus subcarpetas `/frontend/`). 
Ninguno de los chips front-first actuales golpea agresivamente una base de datos local Python todavía. Esto nos permite un crecimiento incremental: los chips funcionan offline o en Session Storage primero.

## 4. Qué queda documentado para ejecución futura (Pendientes)
* **La Anomalía Lingua (`modules/lingua`)**: El orquestador posee un `if` quemado (*hardcoded*) en `backend/main.py` para forzar la lectura del router API y carpetas UX desde `modules/lingua` en vez del formato estándar `chips/chip-{nombre}/`.
* **Migración Pendiente API Routing**: Reacomodar toda la capa de conectividad LLM de `/lingua/services` y `/lingua/api` dentro o referenciada lógicamente por el nuevo `chips/chip-idiomas-ia/api/`. Una vez logrado, se deshabilitará el `if module_name == "lingua"` del bucle de inicialización del archivo principal, logrando al 100% que todo fluya bajo conveción `chip-`.
