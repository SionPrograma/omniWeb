import subprocess
from pathlib import Path
from ..models.lingua_config import settings

class AudioConverter:
    @staticmethod
    def extract_audio(video_path: Path, job_id: str) -> Path:
        audio_path = settings.TEMP_DIR / f"{job_id}_audio.wav"
        command = [
            'ffmpeg', '-i', str(video_path),
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            str(audio_path), '-y'
        ]
        subprocess.run(command, check=True, capture_output=True)
        return audio_path
