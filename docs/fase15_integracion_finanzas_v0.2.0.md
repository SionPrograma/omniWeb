# Primera Integración Backend en Chip Finanzas (OmniWeb v0.2.0)
ADR: Fase 5b - Conexión Cliente-Servidor Transicional

## 1. Misión y Contexto
Al cierre de la arquitectura v0.2.0, el `chip-finanzas` era totalmente funcional a nivel Web (UI/UX) gracias a su lógica Vanilla JS y el mecanismo global de persistencia efímera basado en memoria de navegador (`stateManager.js`). Para evolucionar hacia una plataforma en lugar de solo templates front-end, era necesario instaurar una primera conexión limpia con FastAPI respetando las directrices inquebrantables de no usar React ni destrozar el código viejo.

## 2. Decisión Arquitectónica y Punto de Integración
Al no existir infraestructura de bases de datos relacionales maduras en esta fase, la integración mínima e inteligente se definió apoyándose en:
- El uso nativo del archivo `router.py` en la ruta estandarizada `chips/chip-finanzas/core/router.py`.
- Una **Base de datos transicional In-Memory** (una simple variable Global de tipo Lista en Python) para que los guardados prevalezcan únicamente durante el ciclo de vida del *Runtime* del Servidor, demostrando las capacidades reales de Fetching.

## 3. Implementación Subyacente
### Backend (Módulos Pydantic y API)
- Se desarrolló el paquete de Python `chips/chip-finanzas/core` insertando los exports obligatorios (`__init__.py`).
- En el `router.py`, se expusieron dos endpoints bajo los dominios preconfigurados del middleware principal:
  - `GET /api/v1/finanzas/transactions`: Devuelve movimientos precargados en el servidor en vez de aquellos por default del front-end.
  - `POST /api/v1/finanzas/transactions`: Serializa a dict el movimiento enviado por la UI agregando un ID temporal y lo embuta en el `MOCK_DB`.

### Frontend (Lógica Asíncrona Robusta)
En el archivo `chips/chip-finanzas/frontend/app.js`:
- El inicializador (Boot) ha mutado a `async function init()`. 
- Ahora levanta el JSON desde la ruta API en red.
- **Doble blindaje MPA:** Todos los `fetch` de lectura y escritura (`addTransaction`) conviven dentro de un muro `try/catch`. Ante cualquier pánico de servidor HTTP o deshabilitación de FastAPI por problemas de red, el sistema automáticamente devuelve al chip al comportamiento tradicional de la v0.2.0 (*Fallback local al LocalStorage*), conminando que la UX transaccional jamás se entorpezca para el usuario. 

## 4. Pendientes para el Roadmap (Migraciones Futuras)
*(Documentar ahora, ejecutar después)*

1. **Persistencia Verdaderamente Viva:** Cuando el servidor Uvicorn se recarga, los movimientos creados recientemente se borran para la DB-En-Memoria. Un salto crucial para la Fase 3 del Servidor será enganchar esos Modelos Pydantic hacia PostgreSQL, SQLite u ORMs como SQLAlchemy.
2. **Eliminaciones y Ediciones (CRUD Entero):** Actualmente el punto de integración inicial es Append/Read. Quedará pendiente dotar a UI y API del ciclo de eliminación asincrónica de transacciones.
