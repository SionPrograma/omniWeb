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
from backend.core.creator_control.manager import creator_control_manager
from backend.core.cluster.manager import cluster_manager
from backend.core.ai_host.memory.mission_manager import mission_manager
from .models import SystemState, SystemHealth, ChipState, SystemMode

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

    async def get_state(self, force_refresh: bool = False, user_id: Optional[str] = None):
        if force_refresh or not self._state or (time.time() - self._last_update > self._cache_ttl):
            await self.update_state(user_id=user_id)
        return self._state

    async def update_state(self, user_id: Optional[str] = None):
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

            # 2. Chips & Health (Runtime Alignment)
            all_chips = module_registry.discover_all_chips()
            chip_states = []
            overall_health = SystemHealth.HEALTHY

            for c in all_chips:
                slug = c.get("slug", "unknown")
                reg_info = module_registry.get_module_data(slug)
                
                # Default values from metadata
                health_val = c.get("health", "unverified")
                status_val = "registered" if c.get("active") else "disabled"
                
                # Override with runtime truth if registered
                if reg_info:
                    # Registry exists
                    health_val = reg_info.get("health", health_val)
                    status_val = reg_info.get("status", status_val)
                    
                    # Detection of "Partial Health": claimed backend but not loaded
                    if c.get("has_backend") and not reg_info.get("prefix"):
                        # Mark as warning if it claims backend but is only "frontend-only" or "none"
                        status_val = "unloaded_backend"
                        if health_val != "error":
                            health_val = "warning"
                else:
                    # Discovered on disk but NO trace in registry
                    if c.get("active"):
                        # If it should be active but isn't registered, it's a failure
                        status_val = "registration_failed"
                        health_val = "error"

                # Convert health to enum
                health_enum = SystemHealth.HEALTHY
                if health_val == "warning": 
                    health_enum = SystemHealth.WARNING
                    if overall_health != SystemHealth.ERROR: overall_health = SystemHealth.WARNING
                elif health_val == "error": 
                    health_enum = SystemHealth.ERROR
                    overall_health = SystemHealth.ERROR

                chip_states.append(ChipState(
                    slug=slug,
                    name=c.get("name", "Unknown Chip"),
                    status=status_val,
                    health=health_enum,
                    last_execution=reg_info.get("last_execution", "never") if reg_info else "never",
                    metadata=c
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

            # 5b. Governance & Mode
            mode = await creator_control_manager.get_system_mode()
            maint = await creator_control_manager.get_active_maintenance()
            announcement = await creator_control_manager.get_active_announcement()

            # 5c. Cluster State (Phase 24)
            cluster_state = await cluster_manager.get_cluster_state()
            cluster_info = {
                "active_nodes": cluster_state.active_nodes,
                "total_nodes": cluster_state.total_nodes,
                "cluster_load": cluster_state.cluster_load,
                "nodes": [n.dict() for n in cluster_state.nodes]
            }

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

            # 6b. Active Mission (MissionState Integration)
            active_mission = None
            try:
                mission = mission_manager.get_active_mission()
                if mission:
                    active_mission = mission.model_dump()
            except:
                pass

            # 7. Build Unified State
            self._state = SystemState(
                version=settings.VERSION,
                system_mode=mode,
                maintenance_info=maint,
                announcement=announcement,
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
                cluster=cluster_info,
                sync_status=self._get_sync_info(user_id) if user_id else None,
                active_mission=active_mission,
                timestamp=time.time(),
                uptime_seconds=time.time() - self._start_time
            )
            self._last_update = time.time()
            return self._state
        except Exception as e:
            logger.error(f"Failed to update System State: {e}")
            raise e

    def _get_sync_info(self, user_id: str) -> Dict[str, Any]:
        """Helper to get sync status without redundant manager imports."""
        try:
            with db_manager.get_connection() as conn:
                devices = conn.execute("SELECT COUNT(*) as count FROM sync_devices WHERE user_id = ?", (user_id,)).fetchone()
                last_log = conn.execute(
                    "SELECT timestamp, status FROM sync_audit_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
                    (user_id,)
                ).fetchone()
                
                return {
                    "devices_count": devices["count"] if devices else 0,
                    "last_sync": last_log["timestamp"] if last_log else None,
                    "status": last_log["status"] if last_log else "unconfigured"
                }
        except:
            return {"devices_count": 0, "status": "error"}

state_engine = SystemStateEngine()
