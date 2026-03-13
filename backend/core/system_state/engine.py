import time
import logging
import asyncio
from typing import Dict, Any, List, Optional
from backend.core.config import settings
from backend.core.module_registry import module_registry
from backend.core.database import db_manager
from backend.core.system_auditor.auditor import auditor
from backend.core.system_auditor.fix_engine import fix_engine
from backend.core.master_logbook.manager import master_logbook_manager
from backend.core.master_logbook.models import EntryType, MasterLogbookFilter
from backend.core.permissions import set_chip_context
from .models import SystemState, SystemHealth, ChipState

logger = logging.getLogger(__name__)

class SystemStateEngine:
    """
    Unified System State Engine for OmniWeb.
    Acts as the single source of truth for system health and status.
    """
    def __init__(self):
        self._state: Optional[SystemState] = None
        self._last_update = 0
        self._cache_ttl = 5 # 5 seconds cache
        self._start_time = time.time()
        self._git_info = {"branch": "unknown", "commit": "unknown"}
        self._init_static_data()

    def _init_static_data(self):
        """Pre-fetch data that rarely changes."""
        snapshot = master_logbook_manager.get_system_snapshot()
        self._git_info["branch"] = snapshot.get("git_branch", "unknown")
        self._git_info["commit"] = snapshot.get("last_commit", "unknown")

    async def get_state(self, force_refresh: bool = False) -> SystemState:
        """Returns the current system state, updating if cache expired."""
        from backend.core.permissions import enforce_permission, SYSTEM_STATE_ACCESS
        enforce_permission(SYSTEM_STATE_ACCESS)
        now = time.time()
        if self._state is None or force_refresh or (now - self._last_update > self._cache_ttl):
            await self.update_state()
        return self._state

    async def update_state(self):
        """Aggregates status from all subsystems into a unified state object."""
        try:
            # 1. Database Status
            db_ok = False
            try:
                with set_chip_context("core"):
                    with db_manager.get_connection() as conn:
                        conn.execute("SELECT 1")
                        db_ok = True
            except: pass

            # 2. Chips & Health
            all_chips = module_registry.discover_all_chips()
            chip_states = []
            overall_health = SystemHealth.HEALTHY

            for c in all_chips:
                h = c.get("health", "healthy")
                health_enum = SystemHealth.HEALTHY
                if h == "warning": 
                    health_enum = SystemHealth.WARNING
                    if overall_health != SystemHealth.ERROR: overall_health = SystemHealth.WARNING
                elif h == "error": 
                    health_enum = SystemHealth.ERROR
                    overall_health = SystemHealth.ERROR
                
                chip_states.append(ChipState(
                    slug=c.get("slug", "unknown"),
                    name=c.get("name", "Unknown Chip"),
                    status="active" if c.get("active") else "disabled",
                    health=health_enum,
                    last_execution=c.get("last_execution", "never"),
                    metadata=c # Pass full metadata from module discovery
                ))

            # 3. Auditor Summary
            latest_audit = None
            try:
                filters = MasterLogbookFilter(type=EntryType.SYSTEM_AUDIT)
                entries = master_logbook_manager.get_entries(filters=filters, limit=1)
                if entries:
                    latest_audit = entries[0].metadata.get("audit_report")
                    if latest_audit and latest_audit.get("overall_status") == "ERROR":
                        overall_health = SystemHealth.ERROR
                    elif latest_audit and latest_audit.get("overall_status") == "WARNING" and overall_health != SystemHealth.ERROR:
                        overall_health = SystemHealth.WARNING
            except: pass

            # 4. Auto-Fix Engine
            pending_fixes = list(fix_engine.active_proposals.values())
            is_healing = fix_engine.is_active

            # 5. Memory Usage
            memory_info = {}
            try:
                import psutil
                process = psutil.Process()
                mem = process.memory_info()
                memory_info = {
                    "rss_mb": round(mem.rss / (1024 * 1024), 2),
                    "vms_mb": round(mem.vms / (1024 * 1024), 2),
                    "percent": psutil.virtual_memory().percent
                }
            except ImportError:
                memory_info = {"rss_mb": 0, "status": "psutil not installed"}
            except Exception as e:
                logger.error(f"Failed to get memory info: {e}")

            # 6. Dependency Flow Detection
            flow_data = {
                "ai_to_chips": {
                    "health": overall_health,
                    "latency": 45, # Simulated latency in ms
                    "active": True
                },
                "auditor_to_fixer": {
                    "health": SystemHealth.HEALTHY if not is_healing else "healing",
                    "latency": 12,
                    "active": True
                },
                "fixer_to_chips": {
                    "health": "healing" if is_healing else SystemHealth.HEALTHY,
                    "latency": 88 if is_healing else 0,
                    "active": is_healing
                },
                "ai_to_logbook": {
                    "health": SystemHealth.HEALTHY,
                    "latency": 5,
                    "active": True
                },
                "chips_to_state": {
                    "health": overall_health,
                    "latency": 15,
                    "active": True
                }
            }

            # 7. Build Unified State
            self._state = SystemState(
                version=settings.VERSION,
                system_mode=settings.OMNIWEB_MODE,
                git_branch=self._git_info["branch"],
                git_commit=self._git_info["commit"],
                health=overall_health,
                ai_host={
                    "status": "online",
                    "mode": "hybrid",
                    "processors": ["knowledge", "memory", "graph", "supercommand", "logbook", "code_control", "healing"]
                },
                database={
                    "connected": db_ok,
                    "status": "online" if db_ok else "offline"
                },
                chips=chip_states,
                auditor_summary=latest_audit,
                pending_fixes=len(pending_fixes),
                is_healing=is_healing,
                memory_usage=memory_info,
                flow_data=flow_data,
                timestamp=time.time(),
                uptime_seconds=time.time() - self._start_time
            )
            self._last_update = time.time()
            return self._state
        except Exception as e:
            logger.error(f"Failed to update System State: {e}")
            raise e

state_engine = SystemStateEngine()
