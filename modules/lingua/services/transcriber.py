import whisper
from pathlib import Path
from ..models.lingua_config import settings
import gc
import torch

class Transcriber:
    def __init__(self):
        self.model = None

    def get_model(self):
        if self.model is None:
            # Respect CPU_FRIENDLY_MODE: explicitly specify cpu if set
            device = "cpu" if settings.CPU_FRIENDLY_MODE or not torch.cuda.is_available() else "cuda"
            self.model = whisper.load_model(settings.WHISPER_MODEL, device=device)
        return self.model

    def transcribe(self, audio_path: Path) -> dict:
        model = self.get_model()
        result = model.transcribe(str(audio_path), verbose=False)
        
        # Aggressive memory cleanup option
        if settings.CPU_FRIENDLY_MODE:
            self._cleanup_memory()
            
        return result

    def _cleanup_memory(self):
        # Delete model instance and force garbage collection to free RAM
        if self.model is not None:
            del self.model
            self.model = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
