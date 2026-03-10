# OmniWeb Video Translator

Una solución profesional de **IA para traducción y doblaje automático** de videos. Este proyecto permite transformar contenido audiovisual de YouTube o archivos locales a múltiples idiomas, generando subtítulos sincronizados y una nueva pista de voz mediante clonación de voz.

## Features
- **Descarga Inteligente**: Soporte para URLs de YouTube y carga de archivos locales (MP4, AVI, MOV, MKV).
- **Transcripción de Alta Precisión**: Motor basado en OpenAI Whisper para generar texto y timestamps exactos.
- **Traducción Automática**: Integración con servicios de traducción por segmentos para mantener la integridad temporal.
- **Doblado IA (TTS)**: Generación de voz sintética mediante Coqui TTS con soporte para clonación de voz (XTTS v2).
- **Subtítulos Sincronizados**: Generación automática de archivos SRT en el idioma destino.
- **Merge Final**: Fusión mediante FFmpeg que reemplaza el audio manteniendo la calidad de video original sin pérdida.

## Arquitectura
El proyecto utiliza un pipeline modular orquestado:

`Video Source` → `Audio Extraction` → `AI Transcription` → `Segment Translation` → `AI Voice Synthesis` → `SRT Generation` → `Final Video Merge`

## Stack Tecnológico

### Backend
- **Python 3.11**: Lenguaje base para el procesamiento de datos y modelos de ML.
- **FastAPI**: Backend web de alto rendimiento para la API y gestión de tareas en background.

### IA / Procesamiento
- **Whisper**: Transcripción y detección de lenguaje.
- **Coqui TTS**: Síntesis de voz avanzada y clonación.
- **LibreTranslate**: Motor de traducción de código abierto.

### Herramientas de Sistema
- **FFmpeg**: Manipulación de streams de audio y video.
- **yt-dlp**: Motor de descarga de contenido multimedia.

### Frontend
- **HTML5 / Vanilla JavaScript**: Interfaz limpia, reactiva y sin frameworks pesados.
- **Modern CSS**: Diseño técnico, minimalista y profesional.

## Instalación

### Requisitos Previos
- **Python 3.11** (Requerido para compatibilidad con Whisper y TTS). Descárgalo de [python.org](https://www.python.org/downloads/).
- **FFmpeg** instalado en el sistema y añadido al PATH.

### Configuración Rápida (Recomendado)

Si estás en Windows, puedes usar los scripts automatizados:

1. **Instalar dependencias**: Ejecuta `setup_env_py311.bat`. Este script creará el entorno virtual `.venv` y descargará todo lo necesario.
2. **Arrancar backend**: Ejecuta `run_backend_py311.bat`.

### Configuración Manual

1. **Crear entorno virtual**:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Instalar dependencias**:
   ```powershell
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

### Ejecución Manual

1. **Arrancar el Backend**:
   ```powershell
   cd backend
   python -m app.main
   ```

2. **Acceder a la Interfaz**:
   Abre tu navegador en [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Estado del Proyecto
Versión actual: **v1.0 (MVP Funcional)**  
Este proyecto es una pieza central del ecosistema **OmniWeb**, enfocado en la automatización de flujos de trabajo multimedia.

## Roadmap

### v1.1
- Optimización de tiempos en el pipeline mediante procesamiento paralelo.
- Selección dinámica de voces y estilos de narración.
- Editor de subtítulos integrado en el frontend.

### v2.0
- Sincronización labial (Lip-sync) avanzada.
- Soporte para streaming mediante WebSockets.
- Gestión de usuarios y persistencia de proyectos en base de datos.
