import os
import shutil
import sys
from backend.core.config import settings
from backend.core.logger import logger

def run_self_checks():
    """
    Initializes system self-checks to ensure runtime stability.
    """
    logger.info("--- Starting OmniWeb Self-Checks ---")
    
    # 1. Environment Check
    logger.info(f"Platform: {sys.platform}")
    
    # 2. Directory Checks
    data_dir = os.path.dirname(settings.DATABASE_URL)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "backups"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "migrations"), exist_ok=True)
    
    # 3. Security Checks
    if settings.ADMIN_TOKEN == "omniweb-dev-secret-token":
        logger.warning("SECURITY: Using default ADMIN_TOKEN. Please change this in production.")
    
    # 4. Storage Checks
    total, used, free = shutil.disk_usage(".")
    free_mb = free // (1024 * 1024)
    if free_mb < 500:
        logger.warning(f"STORAGE: Low disk space: {free_mb}MB remaining.")
    else:
        logger.info(f"Storage OK: {free_mb}MB free.")

    logger.info("--- Self-Checks Complete ---")
    return True
