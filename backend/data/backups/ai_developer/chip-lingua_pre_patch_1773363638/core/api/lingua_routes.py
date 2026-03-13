from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from ..models.requests import TranslationRequest, TextTranslateRequest
from ..models.responses import JobResponse, JobDetailResponse, TextTranslateResponse
from ..services.job_manager import job_manager
from ..services.lingua_pipeline import processing_service
from ..models.lingua_config import settings
import os
from pathlib import Path

router = APIRouter(prefix="/process", tags=["process"])

ALLOWED_LANGUAGES = ["es", "en", "fr", "de", "it", "pt"]

@router.post("/", response_model=JobResponse)
async def start_process(
    background_tasks: BackgroundTasks,
    url: str = Form(None),
    target_lang: str = Form("es"),
    file: UploadFile = File(None)
):
    # Validation
    if not url and not file:
        raise HTTPException(status_code=400, detail="Debes proporcionar una URL de YouTube o subir un archivo de video.")
    
    if target_lang not in ALLOWED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Idioma no soportado. Idiomas permitidos: {', '.join(ALLOWED_LANGUAGES)}")

    job_id = job_manager.create_job()
    file_path = None

    if file:
        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Usa MP4, AVI, MOV o MKV.")
            
        file_path = settings.TEMP_DIR / f"{job_id}{ext}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
    # Centralized processing service
    background_tasks.add_task(
        processing_service.run_pipeline, 
        job_id, 
        url, 
        file_path, 
        target_lang
    )
    
    return JobResponse(job_id=job_id, message="Proceso de traducción iniciado.")

@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="El ID del trabajo no existe.")
    
    return JobDetailResponse(**job)

@router.post("/text", response_model=TextTranslateResponse)
async def translate_text(req: TextTranslateRequest):
    """
    Endpoint de transición v0.2.0 para habilitar la interfaz de Chip-Idiomas-IA.
    Por ahora realiza un procesamiento local en backend (mock) como prueba de conexión
    red/arquitectura, preparando el terreno para conectar la IA (Ollama/Groq) real.
    """
    clean_text = req.text.strip().lower()
    return TextTranslateResponse(
        translation=f"[Backend {req.target_lang.upper()}] {req.text}",
        transliteration="-".join(req.text.split()) + "-[syl]",
        pronunciation=f"/{clean_text}/"
    )
