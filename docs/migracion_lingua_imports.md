# Informe de Saneamiento de Imports — Módulo Lingua

Este informe detalla los ajustes realizados en el módulo `Lingua` para asegurar su coherencia estructural dentro de `01-omniweb/modules/lingua`.

## 1. Archivos Modificados

Se han ajustado los siguientes archivos para corregir imports rotos y referencias de rutas:

- `modules/lingua/api/lingua_routes.py`
- `modules/lingua/services/audio_converter.py`
- `modules/lingua/services/downloader.py`
- `modules/lingua/services/file_utils.py`
- `modules/lingua/services/lingua_pipeline.py`
- `modules/lingua/services/transcriber.py`
- `modules/lingua/services/translator.py`
- `modules/lingua/services/tts_generator.py`
- `modules/lingua/models/lingua_config.py`

## 2. Cambios de Import (Original → Nuevo)

| Archivo | Import Original | Import Nuevo | Razón |
| :--- | :--- | :--- | :--- |
| Múltiples (services/*) | `from ..config import settings` | `from ..models.lingua_config import settings` | Reubicación de la configuración al sub-módulo `models`. |
| `lingua_routes.py` | `from ..services.process import ...` | `from ..services.lingua_pipeline import ...` | El archivo fue renombrado durante la migración. |
| `lingua_pipeline.py` | `from ..utils.file_utils import ...` | `from .file_utils import ...` | `file_utils.py` ahora reside dentro de `services/`. |
| `lingua_config.py` | `Path(...).parent.parent.parent` | `Path(...).parent.parent.parent.parent` | Ajuste de `PROJECT_ROOT` para apuntar a la raíz de `01-omniweb`. |

## 3. Referencias No Resueltas / Hallazgos

- **Scripts de UI Faltantes**: `ui/index.html` referencia `js/api.js`, `js/ui.js` y `js/app.js`. Sin embargo, estos archivos **no están presentes** en la carpeta `modules/lingua/ui/js/`. La migración anterior reportó haber copiado `main.js`, pero el origen contiene estos tres archivos.
- **Ausencia de `__init__.py`**: Ninguna de las subcarpetas (`api`, `models`, `services`) contiene un archivo `__init__.py`. Esto puede causar problemas al intentar importar el módulo desde el exterior si no se gestiona el `PYTHONPATH`.

## 4. Dependencias Externas Requeridas

El módulo requiere que el entorno de OmniWeb provea:
- `fastapi`, `pydantic`, `pydantic-settings`
- `openai-whisper`
- `TTS` (Coqui)
- `yt-dlp`
- `deep-translator`
- `torch`, `torchaudio`
- `ffmpeg` instalado en el sistema.

## 5. Próximo Micro-paso Recomendado

**Saneamiento de UI y Estructura**:
1. Copiar los archivos JS faltantes (`api.js`, `ui.js`, `app.js`) desde el proyecto origen a `modules/lingua/ui/js/`.
2. Crear archivos `__init__.py` vacíos en todas las subcarpetas del módulo para formalizar el paquete Python.
3. Realizar una prueba de carga del enrutador en un `main.py` temporal para validar que no existan errores de importación en tiempo de ejecución.
