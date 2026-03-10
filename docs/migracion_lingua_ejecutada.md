# Migración Módulo Lingua (Ejecutada)

Este documento detalla la primera migración mínima viable de recursos útiles identificados para la construcción del módulo `Lingua` en OmniWeb v1.0.0. A continuación, se explican las acciones realizadas, garantizando un proceso ordenado, sin mover ni borrar datos originales y de manera 100% reversible.

## 1. Archivos Copiados (Origen → Destino)

El proyecto satélite original, **OmniWeb-VideoTranslator-MVP**, fue detectado como la base ideal de recursos para los servicios de transcripción, traducción y síntesis de voz (TTS).

**Origen Base:** `...\02-trabajo\portafolio\proyectoOmniwebAntigravity\OmniWeb-VideoTranslator-MVP`  
**Destino Base:** `...\07-proyectosGrandes\01-omniweb\modules\lingua`

### API (Rutas / Endpoints)
- `backend/app/routes/process.py` → `api/lingua_routes.py` *(renombrado para mayor claridad del sub-módulo sobre el pipeline)*
- `backend/app/routes/health.py` → `api/health.py`

### Servicios Básicos (Core de Lingua)
- `backend/app/services/audio_converter.py` → `services/audio_converter.py`
- `backend/app/services/audio_merger.py` → `services/audio_merger.py`
- `backend/app/services/downloader.py` → `services/downloader.py`
- `backend/app/services/job_manager.py` → `services/job_manager.py`
- `backend/app/services/process.py` → `services/lingua_pipeline.py` *(renombrado para diferenciarlo de la ruta HTTP y representar el orquestador general)*
- `backend/app/services/subtitle_generator.py` → `services/subtitle_generator.py`
- `backend/app/services/transcriber.py` → `services/transcriber.py`
- `backend/app/services/translator.py` → `services/translator.py`
- `backend/app/services/tts_generator.py` → `services/tts_generator.py`
- `backend/app/utils/file_utils.py` → `services/file_utils.py` *(asignado a utilities del servicio)*

### Modelos y Configuración
- `backend/app/models/requests.py` → `models/requests.py`
- `backend/app/models/responses.py` → `models/responses.py`
- `backend/app/config.py` → `models/lingua_config.py` *(renombrado y movido ya que contiene configuraciones específicas de Lingua)*

### UI (Frontend)
- `frontend/index.html` → `ui/index.html`
- `frontend/css/style.css` → `ui/css/style.css`
- `frontend/js/main.js` → `ui/js/main.js`

### Documentación Histórica (Referencia)
- `README.md` → `docs/omniweb_MVP_README.md`
- `README_BACKEND.md` → `docs/omniweb_MVP_BACKEND.md`
- `README_FRONTEND.md` → `docs/omniweb_MVP_FRONTEND.md`
- `project_tree.txt` → `docs/MVP_tree.txt`

## 2. Archivos Omitidos

Como la estructura debe mantenerse limpia y solo incluir lo estrictamente necesario para el módulo, no se ha replicado un empaquetado de proyecto completo:
- `backend/app/main.py`: Omitido, ya que el archivo de arranque (Entrypoint) general será gestionado centralizadamente por OmniWeb.
- `requirements.txt`: Omitido en la carpeta del submódulo. Las dependencias formarán parte del marco macro de OmniWeb.
- `.env` / `.env.example`: Omitidos. La configuración de entorno se leerá desde el contexto central del proyecto.
- Archivos `.bat` y `.gitignore`: Excluidos, son irrelevantes en la base del módulo interno y corresponden a un contexto superior de deployment.

## 3. Dependencias Faltantes (Requisitos en Node/Python Master)

Para que el backend de *Lingua* corra sin errores de importación dentro de OmniWeb, se deberá asegurar proveer en el entorno master:

- **Ecosistema General:** `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
- **Herramientas Multimedia:** `yt-dlp` (descarga), `ffmpeg-python` (conversiones multimedia de bajo nivel).
- **Procesamiento NLP / Audio:**
  - `openai-whisper`
  - `TTS` (Coqui TTS u otros fallbacks)
  - `deep-translator` (u otras traducciones implementadas)
  - `torch`, `torchaudio`

## 4. Próximos Pasos para Funcionalidad

1. **Actualización de Imports Relativos/Absolutos:** Los archivos provenientes del MVP original invocan módulos usando el path base antiguo (e.g. `import app.services...`). Se deberá realizar un factoraje simple que redireccione al nuevo espacio de nombres local en OmniWeb (`from modules.lingua.services import ...`).
2. **Inclusión de Enrutador:** Enganchar `api/lingua_routes.py` dentro del `main.py` futuro de toda la plataforma OmniWeb usando `app.include_router()`.
3. **Orquestación Global (Job Manager):** Evaluar unificar o mejorar el `job_manager.py` para usar bases de datos duraderas en lugar de memoria RAM, y alinearse al diseño base de componentes compartidos de OmniWeb.
4. **Refactorización de Rutas Frontales:** El `index.html` copiado espera que funcione como web inicial independiente. Debatir si será servido en vistas injertadas (`iframes`), `components` nativos de react/vue o bajo rutas HTML simples como base temporal.
