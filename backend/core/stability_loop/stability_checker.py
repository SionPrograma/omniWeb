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
        }
        
        is_stable = all(results.values())
        return {"is_stable": is_stable, "details": results}

    async def check_health(self) -> bool:
        import requests
        try:
            resp = requests.get(f"{self.base_url}/api/v1/system/health", timeout=5.0)
            return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception as e:
            logger.error(f"Stability check failed: Health endpoint unreachable: {e}")
            return False

    async def check_stats(self) -> bool:
        import requests
        try:
            resp = requests.get(f"{self.base_url}/api/v1/system/stats", timeout=5.0)
            return resp.status_code == 200
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
        import requests
        try:
            resp = requests.get(f"{self.base_url}/api/v1/system/chips", timeout=5.0)
            if resp.status_code == 200:
                chips = resp.json()
                return len(chips) > 0
            return False
        except Exception:
            return False

stability_checker = StabilityChecker()
