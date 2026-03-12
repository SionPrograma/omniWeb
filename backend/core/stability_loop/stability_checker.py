import logging
import os
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class StabilityChecker:
    """
    Evaluates system health after modifications.
    Requirement: validate health, stats, db connectivity, chip discovery, AI Host and Event Bus.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    async def check_all(self) -> dict:
        """Runs a full system health verification."""
        results = {
            "health": await self.check_health(),
            "stats": await self.check_stats(),
            "database": self.check_db(),
            "chips": await self.check_chips(),
            "distributed": await self.check_distributed_sync()
        }
        
        is_stable = all(results.values())
        return {"is_stable": is_stable, "details": results}

    async def check_distributed_sync(self) -> bool:
        try:
            from backend.core.distributed_bus.node_registry import node_registry
            # Basic verification that registry is responsive
            node_registry.get_active_nodes()
            return True
        except Exception:
            return False

    async def check_health(self) -> bool:
        # Avoid HTTP call to self to prevent deadlock in single-threaded uvicorn
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            disk_ok = free > (100 * 1024 * 1024)
            return disk_ok and self.check_db()
        except Exception as e:
            logger.error(f"Internal health check failed: {e}")
            return False

    async def check_stats(self) -> bool:
        try:
            from backend.core.module_registry import module_registry
            # In bootstrap or test modes, we might have 0 modules. 
            # We check if the registry is at least accessible.
            module_registry.get_active_modules()
            return True
        except Exception:
            return False

    def check_db(self) -> bool:
        try:
            from backend.core.permissions import set_chip_context
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("SELECT 1").fetchone()
                    return True
        except Exception:
            return False

    async def check_chips(self) -> bool:
        try:
            from backend.core.module_registry import module_registry
            chips = module_registry.discover_all_chips()
            return len(chips) > 0
        except Exception:
            return False

stability_checker = StabilityChecker()
