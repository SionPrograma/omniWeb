import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..models.lingua_config import settings
from .job_store import SQLiteJobStore

class JobManager:
    """
    Durable State Management for chip-lingua.
    Uses SQLite as source of truth with an in-memory cache for hot jobs.
    """
    def __init__(self):
        self.store = SQLiteJobStore(settings.DB_PATH)
        # In-memory cache for active jobs (polling optimization)
        self.jobs: Dict[str, Dict[str, Any]] = self.store.load_all_jobs()

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "stage": "initialization",
            "stage_completed": None,
            "percent": 0.0,
            "message": "Job created",
            "progress_history": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result_url": None,
            "error": None
        }
        self.jobs[job_id] = job_data
        self.store.save_job(job_data)
        return job_id

    def update_job(
        self, 
        job_id: str, 
        stage: str, 
        percent: float, 
        message: str, 
        result_url: Optional[str] = None, 
        error: Optional[str] = None, 
        stage_completed: Optional[str] = None,
        status: Optional[str] = None
    ):
        if job_id not in self.jobs:
            # Try to restore from store if missing in memory (restart case)
            stashed_job = self.store.get_job(job_id)
            if stashed_job:
                self.jobs[job_id] = stashed_job
            else:
                return
        
        job = self.jobs[job_id]
        updated_at = datetime.now().isoformat()
        job["updated_at"] = updated_at
        job["stage"] = stage
        job["percent"] = percent
        job["message"] = message
        
        if stage_completed:
            job["stage_completed"] = stage_completed
            
        if result_url:
            job["result_url"] = result_url
            
        if error:
            job["error"] = error
            
        if status:
            job["status"] = status
        else:
            if error:
                job["status"] = "failed"
            elif percent >= 100.0 and stage == "complete":
                if job.get("status") == "partial_success":
                    job["status"] = "partial_success"
                else:
                    job["status"] = "completed"
                    job["stage_completed"] = "complete"
            elif job.get("status") != "partial_success":
                job["status"] = "processing"

        # Durable Audit Log (Section C/F)
        event = {
            "status": job["status"],
            "stage": stage,
            "percent": percent,
            "message": message,
            "timestamp": updated_at
        }
        
        # In-memory history cache
        if "progress_history" not in job: job["progress_history"] = []
        job["progress_history"].append(event)
        
        # Persistent writes
        self.store.save_job(job)
        self.store.add_progress_event(job_id, event)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        is_purged = False
        job = self.jobs.get(job_id)
        if not job:
            job = self.store.get_job(job_id)
            if job: self.jobs[job_id] = job # Re-cache
            else: 
                is_purged = self.store.is_job_purged(job_id)
                if not is_purged: return None
                # Create a placeholder for purged job
                job = {
                    "status": "purged",
                    "stage": "archived",
                    "percent": 0.0,
                    "message": "Job purged by retention policy",
                    "progress_history": [],
                    "result_url": None,
                    "error": None
                }
        
        return {
            "job_id": job_id,
            "status": job["status"],
            "stage": job["stage"],
            "stage_completed": job.get("stage_completed"),
            "percent": job["percent"],
            "message": job["message"],
            "progress": job.get("progress_history", []),
            "result_url": job.get("result_url"),
            "error": job.get("error"),
            "is_purged": is_purged or job.get("status") == "purged"
        }

job_manager = JobManager()
