# Backend Guide ⚙️

## Technologies
- **Framework**: FastAPI
- **Validation**: Pydantic v2
- **Audio Extract**: yt-dlp + ffmpeg
- **ML**: Whisper (OpenAI) + XTTS (Coqui)

## API Endpoints
- `GET /health`: System status.
- `POST /process/`: Submit a translation job (`url`, `target_lang`).
- `GET /process/{job_id}`: Poll for status.
- `GET /outputs/{path}`: Access generated files.

## Environment Variables
Defined in `.env.example`. Make sure to set `TEMP_DIR` and `OUTPUT_DIR` to absolute paths if running in production.
