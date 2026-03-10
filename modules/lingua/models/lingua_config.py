import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# PROJECT_ROOT is where .env and requirements.txt are located
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "OmniWeb VideoTranslator MVP"
    DEBUG: bool = True
    
    # Base paths relative to the project root
    BASE_DIR: Path = PROJECT_ROOT
    OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"
    TEMP_DIR: Path = PROJECT_ROOT / "temp"
    
    # Integration URLs
    LIBRETRANSLATE_URL: str = "http://localhost:5000"
    
    # --- Performance & Memory Configurations ---
    # CPU-friendly mode (forces lighter models and aggressive memory cleanup)
    CPU_FRIENDLY_MODE: bool = True
    
    # Model Names
    # For low-RAM CPU systems, "tiny" is safer, or "base"
    WHISPER_MODEL: str = "tiny" 
    
    # TTS Settings
    TTS_ENABLED: bool = True
    COQUI_TTS_MODEL: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    # To prevent OOM, split translated text into chunks (approx number of characters max per chunk)
    TTS_MAX_CHUNK_LENGTH: int = 250
    # ---------------------------------------------
    
    # Sub-directories for outputs
    AUDIO_OUTPUT: Path = OUTPUT_DIR / "audio"
    SUBTITLE_OUTPUT: Path = OUTPUT_DIR / "subtitles"
    TRANSCRIPT_OUTPUT: Path = OUTPUT_DIR / "transcripts"
    TRANSLATION_OUTPUT: Path = OUTPUT_DIR / "translations"
    MERGED_OUTPUT: Path = OUTPUT_DIR / "merged"

    # Load .env from the project root
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), 
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra fields in .env
    )

    def create_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.OUTPUT_DIR,
            self.TEMP_DIR,
            self.AUDIO_OUTPUT,
            self.SUBTITLE_OUTPUT,
            self.TRANSCRIPT_OUTPUT,
            self.TRANSLATION_OUTPUT,
            self.MERGED_OUTPUT
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.create_directories()
