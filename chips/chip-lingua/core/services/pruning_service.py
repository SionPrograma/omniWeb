import os
from pathlib import Path
from datetime import datetime, timedelta
import logging
from ..models.lingua_config import PROJECT_ROOT, settings
from .job_manager import job_manager

logger = logging.getLogger(__name__)

class PruningService:
    """
    Governance Retention Service for chip-lingua.
    Manages the lifecycle of job metadata and output media.
    Ensures storage remains auditable and sustainable.
    """
    
    def run_policy_pruning(self):
        """Executes the standard retention policy pruning."""
        if not settings.PRUNING_ENABLED:
            logger.info("Pruning is disabled in config.")
            return

        now = datetime.now()
        
        # 1. Identify Stale Completed Jobs
        self._prune_stale_by_status("completed", settings.RETENTION_DAYS_COMPLETED)
        self._prune_stale_by_status("partial_success", settings.RETENTION_DAYS_COMPLETED)
        
        # 2. Identify Stale Failed Jobs
        self._prune_stale_by_status("failed", settings.RETENTION_DAYS_FAILED)
        
        # 3. Orphan File Detection (Advanced Cleanup)
        self.detect_and_clear_orphans()

    def _prune_stale_by_status(self, status: str, days: int):
        threshold = datetime.now() - timedelta(days=days)
        
        # Fetch all jobs to identify stale ones
        # For small pilots, loading all is fine, for large systems use SQL WHERE
        stale_count = 0
        all_jobs = job_manager.store.load_all_jobs()
        
        for job_id, job in all_jobs.items():
            if job["status"] == status:
                updated_at = datetime.fromisoformat(job["updated_at"])
                if updated_at < threshold:
                    self.purge_job(job_id, reason=f"Retention exceeded ({days} days)")
                    stale_count += 1
        
        if stale_count > 0:
            logger.info(f"Pruning: Cleared {stale_count} '{status}' jobs.")

    def purge_job(self, job_id: str, reason: str = "Manual Purge"):
        """Governed removal of a single job and its associated media."""
        job = job_manager.get_job(job_id)
        if not job: return False

        media_paths = []
        # Result URL
        if job.get("result_url"):
            # Result URL might be relative to static or absolute
            p = Path(job["result_url"])
            if not p.is_absolute():
                 # Handle relative URLs (assuming they map to static paths we know)
                 # Most OmniWeb result_urls in Lingua are intended to be served
                 pass
            else:
                 media_paths.append(p)

        # Scoped Cleanup: Try to delete files matching job_id in outputs/
        # This is safer for orphaned/chunk files
        outputs_root = settings.OUTPUT_DIR
        for root, dirs, files in os.walk(outputs_root):
            for f in files:
                if job_id in f:
                    media_paths.append(Path(root) / f)

        # Perform File Deletion
        cleared_any = False
        for mp in set(media_paths):
            if mp.exists():
                try:
                    os.remove(mp)
                    cleared_any = True
                except Exception as e:
                    logger.error(f"Failed to purge file {mp}: {e}")

        # Persistent Audit & DB Deletion
        job_manager.store.log_purge(job_id, job["status"], reason, media_cleared=cleared_any)
        job_manager.store.delete_job(job_id)
        
        # Remove from in-memory cache
        if job_id in job_manager.jobs:
            del job_manager.jobs[job_id]
            
        return True

    def detect_and_clear_orphans(self):
        """Cleans up files in outputs/ that don't belong to any registered job."""
        registered_jobs = set(job_manager.store.load_all_jobs().keys())
        outputs_root = settings.OUTPUT_DIR
        
        orphans_cleared = 0
        for root, dirs, files in os.walk(outputs_root):
            for f in files:
                # Many files in Lingua outputs are named with {job_id}_...
                # We extract the UUID if present and check registration
                import re
                match = re.search(r'([a-f0-9\-]{36})', f)
                if match:
                    fid = match.group(1)
                    if fid not in registered_jobs:
                        fpath = Path(root) / f
                        try:
                            # Only delete files older than 24h to avoid race condition with active jobs
                            mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
                            if mtime < (datetime.now() - timedelta(hours=24)):
                                os.remove(fpath)
                                orphans_cleared += 1
                        except: pass
                        
        if orphans_cleared > 0:
            logger.info(f"Orphan Cleanup: Purged {orphans_cleared} orphaned media files.")

pruning_service = PruningService()
