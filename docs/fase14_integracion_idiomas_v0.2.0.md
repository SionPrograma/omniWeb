# Primera Integración Backend en Chip Idiomas (OmniWeb v0.2.0)
ADR: Fase 5 - Conexión Cliente-Servidor Transicional

## 1. Misión y Contexto
En la arquitectura propuesta para la versión `0.2.0`, el frontend `chip-idiomas-ia` operaba 100% desconectado, simulando comportamientos de traducción mediante diccionarios en memoria o diccionarios quemados en código (*mocks locales*). 
Al mismo tiempo, la lógica pesada de los LLMs e inteligencias de audio (Whisper/Groq) vivía pausada bajo la carpeta intocable `modules/lingua/`. 

Esta fase inicia el proceso orgánico de enhebrar la relación de la UI moderna con su Backend Legacy.

## 2. Decisión Arquitectónica y Punto de Integración
- **Ruta Seleccionada:** `modules/lingua/api/lingua_routes.py`
- **Por qué no moverlo aún:** Refactorizar toda la carpeta de servicios AI (Pydantic / Whisper) a `chips/chip-idiomas-ia/api` requeriría un sprint mayúsculo ajeno al foco mínimo viable actual.
- **Acción:** Se expuso un endpoint **Transicional Simulado** (`POST /api/v1/lingua/process/text`) en el router del legado Lingua. Este mini-endpoint procesa del lado de los clusters Python la información textual e inyecta la cabecera `[Backend {LANG}]` devolviendo diccionarios Pydantic exactos a la interfaz visual.

## 3. Implementación Frontend (Async Fetch)
El javascript del Chip de Idiomas (`chips/chip-idiomas-ia/frontend/app.js`) mutó de síncrono offline a asíncrono híbrido:
1. `handleTranslation` ahora es `async` e incluye bloqueos de UX naturales (ej. "Conectando al backend...").
2. Se intenta despachar el `fetch` contra FastAPI por defecto.
3. Se protegió fuertemente con un bloque `try/catch`. Si el servidor está apagado (ej. desarrollo HTML directo sin Uvicorn) o la API colapsa, el motor *fallbackea* silenciosamente a los *mocks offline locales* agregando la leyenda `[LOCAL]` en pantalla, garantizando el primer mandato MPA: **No rompas la UX**.

## 4. Modelos Transicionales Inyectados
Se han extendido los contratos Python (`modules/lingua/models`):
- `TextTranslateRequest`
- `TextTranslateResponse`

## 5. Pendientes para el Roadmap Subyacente
*(Documentado ahora, para ejecutar después en otra rama/sprint)*

Actualmente, el Request a `/text` tan solo manipula strings de prueba simulando carga remota. 
El verdadero paso siguiente es reemplazar la función interna de `lingua_routes.py` (ahora Mock) por las llamadas a los LLMs genuinos importados de clase `TranslateProvider` que ya existen dormidos en `modules/lingua/services/`.
Al finalizar eso, finalmente Lingua se cerrará y sus routers fluirán orgánicamente bajo la tupla de carpetas de `/chips/`.
