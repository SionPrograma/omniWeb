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
    if not settings.IS_ADMIN_TOKEN_SAFE:
        logger.warning("!!! SECURITY CRITICAL !!!")
        logger.warning("Using default ADMIN_TOKEN. This makes the system extremely vulnerable.")
        logger.warning("Please set OMNIWEB_ADMIN_TOKEN environment variable immediately.")
        
        if os.getenv("OMNIWEB_STRICT_SECURITY", "0") == "1":
            logger.error("STRICT SECURITY MODE: Refusing to start with insecure credentials.")
            sys.exit(1)
    
    # 4. Storage Checks
    total, used, free = shutil.disk_usage(".")
    free_mb = free // (1024 * 1024)
    if free_mb < 500:
        logger.warning(f"STORAGE: Low disk space: {free_mb}MB remaining.")
    else:
        logger.info(f"Storage OK: {free_mb}MB free.")

    logger.info("--- Self-Checks Complete ---")
    return True
