import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
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
            return
        
        job = self.jobs[job_id]
        job["updated_at"] = datetime.now().isoformat()
        job["stage"] = stage
        job["percent"] = percent
        job["message"] = message
        
        if stage_completed:
            job["stage_completed"] = stage_completed
            
        if result_url:
            job["result_url"] = result_url
            
        if error:
            job["error"] = error
            
        # Define status logically if not explicitly provided
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

        # Log to history
        job["progress_history"].append({
            "status": job["status"],
            "stage": stage,
            "percent": percent,
            "message": message,
            "timestamp": job["updated_at"]
        })

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.jobs.get(job_id)
        if not job:
            return None
        return {
            "job_id": job_id,
            "status": job["status"],
            "stage": job["stage"],
            "stage_completed": job["stage_completed"],
            "percent": job["percent"],
            "message": job["message"],
            "result_url": job["result_url"],
            "error": job["error"]
        }

job_manager = JobManager()
