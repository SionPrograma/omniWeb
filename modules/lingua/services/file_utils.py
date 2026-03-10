import os
import shutil
from pathlib import Path
from ..models.lingua_config import settings

def clean_temp_files(job_id: str):
    """Remove temporary files associated with a job."""
    for file in settings.TEMP_DIR.glob(f"{job_id}*"):
        try:
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)
        except Exception as e:
            print(f"Error cleaning up {file}: {e}")

def get_job_dir(base_dir: Path, job_id: str) -> Path:
    """Create and return a directory for a specific job."""
    job_dir = base_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir

def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()
