# OmniWeb v0.2.0 Architecture (ADR-001)

## Contexto y Decisión Estratégica
OmniWeb ha evolucionado orgánicamente desde pequeños experimentos hasta convertirse en un ecosistema de aplicaciones (Chips). Durante la maduración del repositorio, surgió la necesidad de definir un marco de trabajo estable.

Se decidió formalizar la **Arquitectura v0.2.0** bajo los siguientes principios innegociables:
1. **Multi-Page Application (MPA) basada en Módulos:** No se migrará a Single Page Application (SPA), React o Vite. La separación de páginas/chips es natural y robusta. FastApi actúa como orquestador.
2. **Vanilla First:** El frontend se mantiene en Vanilla JS, HTML y CSS para garantizar cero dependencias agresivas, alta durabilidad y un claro principio pedagógico.
3. **Persistencia Local Desacoplada:** El uso del state-manager y nav-system nativos ha probado ser suficiente para la fase actual.
4. **Backend Python Centralizado:** FastAPI orquesta la entrega de archivos estáticos y, a futuro, los micro-endpoints de negocio.

## Resolución de Ambigüedades Estructurales
Para evitar colisiones cognitivas, se definen explícitamente las siguientes convenciones de carpetas:

### 1. El Problema de "Los Dos Cores"
Existen dos directorios llamados `core` con propósitos radicalmente opuestos. En lugar de ejecutar renombres masivos que rompan historiales de Git o paths actuales, se establece por convención:
- **`core/` (Raíz)**: Es el **Frontend Core (Vanilla JS)**. Solo contiene lógica del navegador (`nav-system.js`, `state-manager.js`, utilidades compartidas del DOM). Nunca debe alojar código de negocio backend.
- **`backend/core/`**: Es el **Backend Core (Python)**. Solo contiene la configuración global de FastAPI (`config.py`), el registro del bus de eventos y utilidades de infraestructura del servidor. Nunca sirve JS directamente.

### 2. `chips/` vs `modules/`
- **`chips/`**: Es la convención definitiva y moderna. Alberga las mini-aplicaciones enteras (frontend y a futuro su router api interno). Su estructura es predecible: `chips/{nombre}/frontend`.
- **`modules/`**: Es un directorio **Legacy**. Actualmente contiene sistemas antiguos de backend profundo (como `lingua`, `assistant`, `planner`). El plan a largo plazo (no inmediato) es que las APIs de estos `modules` sean absorbidas por sus equivalentes en `chips/`. **No comenzar nuevos desarrollos dentro de `modules/`**.

### 3. El Alcance de `frontend/`
- A diferencia de arquitecturas SPA donde `/frontend/` aloja todo el proyecto visual, en OmniWeb la carpeta **`frontend/`** es simplemente el "Entrypoint" o "Dashboard Central" (Renderizado en `/`).
- Los componentes visuales de las aplicaciones particulares viven en **`chips/{nombre}/frontend/`**.

## Reglas para Desarrollo Futuro
- Ningún chip interno debe invocar CSS o JS de otro chip directamente (acoplamiento nulo). Todo recurso compartido debe vivir en `core/shared/`.
- Cualquier cambio de estado global debe pasar por `core/state/state-manager.js`.
- El backend (`backend/main.py`) es agnóstico del chip: si está en `config.py -> ACTIVE_MODULES`, simplemente lo monta.

---
*OmniWeb Architecture v0.2.0 - Decisión Consolidada*
