import time
import logging
import asyncio
from datetime import datetime
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
from backend.core.ai_host.memory.resource_lock_manager import resource_lock_manager
from backend.core.ai_host.memory.mission_telemetry import mission_telemetry
from backend.core.ai_host.shadow_swarm.shadow_constructor import shadow_constructor_manager
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
        # Adaptive TTL (Phase 21: Orchestration Fluidity)
        # If we have an active mission, we want faster updates (1s) instead of the default 5s
        is_mission_active = False
        if self._state and self._state.active_mission:
             status = self._state.active_mission.get("status")
             if status in ["OPEN", "ACTIVE", "RECOVERING"]:
                  is_mission_active = True

        current_ttl = 1.0 if is_mission_active else self._cache_ttl
        
        if force_refresh or not self._state or (time.time() - self._last_update > current_ttl):
            await self.update_state(user_id=user_id)
        return self._state

    async def update_state(self, user_id: Optional[str] = None):
        """Aggregates status from all subsystems into a unified state object."""
        # Telemetry & Agregation Defaults
        mission_events = []
        portfolio_pulse = []
        parallel_missions = []
        archived_missions = []
        completed_missions = []
        proposals = []
        resource_locks = []
        active_mission = None
        last_handoff_data = None
        
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
            overall_health = SystemHealth.HEALTHY if db_ok else SystemHealth.WARNING

            for c in all_chips:
                slug = c.get("slug", "unknown")
                reg_info = module_registry.get_module_data(slug)
                
                # Default values from metadata
                # Criterio: Si no está en el registry, está solo 'registered' (pasivo)
                health_val = c.get("health", "unverified")
                status_val = "registered" if c.get("active") else "disabled"
                
                # Dynamic checks (if registered)
                if reg_info:
                    health_val = reg_info.get("health", "unverified")
                    status_val = reg_info.get("status", "active")
                    
                    if c.get("has_backend") and not reg_info.get("prefix"):
                        status_val = "unloaded_backend"
                        if health_val not in ["error", "disabled"]:
                            health_val = "warning"
                else:
                    if c.get("active"):
                        status_val = "unlisted"
                        health_val = "unverified"
                    else:
                        status_val = "disabled"
                        health_val = "deactivated"

                # Map to official SystemHealth Enum (Honest Mapping)
                try:
                    health_enum = SystemHealth(health_val)
                except ValueError:
                    health_enum = SystemHealth.UNKNOWN

                # System wide health propagation
                if health_enum == SystemHealth.ERROR:
                    overall_health = SystemHealth.ERROR
                elif health_enum == SystemHealth.WARNING and overall_health != SystemHealth.ERROR:
                    overall_health = SystemHealth.WARNING
                # UNVERIFIED doesn't necessarily break the whole host, but we keep it sober

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
            # 6. Active Mission Context (Phase 18: MISSION STATE)
            mission = mission_manager.get_active_mission()
            active_mission_id = mission.mission_id if mission else None
            
            # Aggregation defaults (CRITICAL TELEMETRY)
            parallel_missions = []
            archived_missions = []
            completed_missions = []
            mission_events = []
            portfolio_pulse = []
            proposals = []
            resource_locks = []
            
            active_mission = None
            try:
                if mission:
                    active_mission = mission.model_dump()
                    # 6c. Shadow Swarm Proposals for this mission (Phase 30 Saneamiento)
                    shadows = shadow_constructor_manager.get_constructors_for_mission(mission.mission_id)
                    for s in shadows:
                         if s.proposal:
                              prop = s.proposal.model_dump()
                              # Adding metadata for UI buttons
                              prop["proposal_id"] = s.shadow_id
                              prop["action_type"] = "mutation"
                              prop["targets"] = [s.proposal.target_file]
                              proposals.append(prop)
                    
                    # 6d. Extract Mission Hierarchy (Phase 21: MISSION HIERARCHY)
                    hierarchy = {
                        "parent": None,
                        "sub_missions": [],
                        "dependencies": []
                    }
                    if mission.parent_id:
                        p = mission_manager.get_mission_by_id(mission.parent_id)
                        if p: hierarchy["parent"] = {"id": p.mission_id, "goal": p.active_goal, "status": p.status.value}
                    
                    subs = mission_manager.get_sub_missions(mission.mission_id)
                    hierarchy["sub_missions"] = [{"id": s.mission_id, "goal": s.active_goal, "status": s.status.value} for s in subs]
                    
                    for dep_id in mission.dependency_ids:
                        d = mission_manager.get_mission_by_id(dep_id)
                        if d: hierarchy["dependencies"].append({"id": d.mission_id, "goal": d.active_goal, "status": d.status.value})
                    
                    if mission.retried_from:
                        r = mission_manager.get_mission_by_id(mission.retried_from)
                        if r: hierarchy["retried_from"] = {"id": r.mission_id, "goal": r.active_goal, "status": r.status.value}
                    
                    if mission.branched_from:
                        b = mission_manager.get_mission_by_id(mission.branched_from)
                        if b: hierarchy["branched_from"] = {"id": b.mission_id, "goal": b.active_goal, "status": b.status.value}

                    active_mission["hierarchy"] = hierarchy
                
                # 6e. Extract Parallel Running Missions (Phase 21: MISSION PARALLELISM & SCHEDULING)
                running = mission_manager.get_parallel_running_missions()
                parallel_missions = [{
                    "id": m.mission_id, 
                    "goal": m.active_goal, 
                    "status": m.status.value, 
                    "last_focused": m.last_focused_at.isoformat(),
                    "priority_score": m.priority_score,
                    "priority_class": m.priority_class,
                    "readiness_state": m.readiness_state,
                    "compact_digest": m.compact_digest.model_dump() if m.compact_digest else None
                } for m in running if not mission or m.mission_id != mission.mission_id]
                
                # Recommendation Logic (Phase 22: MISSION SCHEDULING)
                # If current focus is low priority but others are high, suggest focus.
                recommended_focus = None
                if running:
                    top_mission = running[0] # Already sorted by PriorityEngine
                    if not mission or top_mission.mission_id != mission.mission_id:
                        recommended_focus = {
                            "id": top_mission.mission_id,
                            "goal": top_mission.active_goal,
                            "reason": f"Misión con prioridad {top_mission.priority_class} ({top_mission.readiness_state})"
                        }
                
                # --- PHASE: MULTI-MISSION SCHEDULER (Phase 88) ---
                schedules = []
                try:
                    from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
                    active_schedules = scheduler_manager.get_all()
                    schedules = [s.model_dump() for s in active_schedules]
                except Exception as sched_err:
                    logger.warning(f"[SYSTEM_STATE_ENGINE] Could not fetch schedules: {sched_err}")
                
                # 6f. Portfolio Summary (Phase: MISSION PORTFOLIO)
                archived = mission_manager.get_archived_missions(limit=10)
                archived_missions = [{"id": m.mission_id, "goal": m.active_goal, "status": m.status.value, "updated": m.updated_at.isoformat()} for m in archived]
                
                completed = mission_manager.get_completed_recent_missions(limit=5)
                completed_missions = [{"id": m.mission_id, "goal": m.active_goal, "status": m.status.value, "updated": m.updated_at.isoformat()} for m in completed]
                
                # 6g. Telemetry Events (Phase: MISSION CRITICAL TELEMETRY)
                mission_events = []
                if active_mission_id:
                    events = mission_telemetry.get_recent_events(active_mission_id, limit=10)
                    mission_events = [e.model_dump(mode='json') for e in events]
                
                pulse = mission_telemetry.get_portfolio_pulse(limit=10)
                portfolio_pulse = [e.model_dump(mode='json') for e in pulse]
                
            except Exception as swarm_err:
                logger.warning(f"[SYSTEM_STATE] Swarm sync failed: {swarm_err}")

            # 8. Extract Recent Handoff (Ergonomics Phase 21)
            last_handoff_data = None
            try:
                filters = MasterLogbookFilter(type=EntryType.MISSION_HANDOFF)
                recent_handoffs = master_logbook_manager.get_entries(filters=filters, limit=1)
                if recent_handoffs:
                    last_handoff_data = recent_handoffs[0].metadata
            except Exception as e:
                logger.warning(f"[SYSTEM_STATE_ENGINE] Could not fetch last handoff: {e}")
            
            # Phase: MISSION CONFLICT RESOLVER - Resource Locks
            resource_locks = []
            try:
                resource_locks = resource_lock_manager.get_all_active_locks()
            except Exception as lock_err:
                logger.warning(f"[SYSTEM_STATE_ENGINE] Could not fetch locks: {lock_err}")

            # 9. Build Unified State
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
                last_handoff=last_handoff_data,
                mission_hierarchy=active_mission.get("hierarchy") if active_mission else None,
                parallel_missions=parallel_missions,
                archived_missions=archived_missions,
                completed_missions=completed_missions,
                mission_events=mission_events,
                portfolio_pulse=portfolio_pulse,
                proposals=proposals,
                resource_locks=resource_locks,
                schedules=schedules,
                recommended_focus=recommended_focus,
                timestamp=datetime.now().isoformat(),
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
