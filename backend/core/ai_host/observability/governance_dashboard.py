import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.memory.mission_models import MissionStatus, MissionState
from backend.core.ai_host.memory.mission_telemetry import mission_telemetry

logger = logging.getLogger(__name__)

class GovernanceDashboard:
    """
    Aggregation Engine for Multi-Mission Governance.
    Consolidates security state, authority sessions, and audit events.
    """

    def _get_quick_actions(self, m: MissionState) -> List[Dict[str, Any]]:
        """
        CAPA 1 & 2: Quick Action Model & Exposure Layer.
        Determines available actions based on mission status and governance state.
        """
        actions = []
        
        # Action IDs and Labels (Criterio Central OmniWeb)
        # 1. Base Navigation (Always available for active/parallel)
        actions.append({
            "id": "switch_focus", "label": "Enfocar", "type": "navigation", 
            "level": "safe", "icon": "🎯"
        })
        
        # 2. Contextual Actions
        if m.status == MissionStatus.BLOCKED:
            actions.append({
                "id": "request_override", "label": "Autorizar", "type": "governance", 
                "level": "governed", "requires_pin": True, "icon": "🔑"
            })
            actions.append({
                "id": "view_risk", "label": "Auditar Riesgo", "type": "inspection", 
                "level": "safe", "icon": "⚖️"
            })
        
        if m.status in [MissionStatus.RUNNING, MissionStatus.OPEN]:
            actions.append({
                "id": "pause_mission", "label": "Pausar", "type": "control", 
                "level": "governed", "requires_confirmation": True, "icon": "⏸️"
            })
            actions.append({
                "id": "request_forecast", "label": "Simular What-If", "type": "simulation", 
                "level": "safe", "icon": "🔮"
            })
            
        if m.status == MissionStatus.PAUSED:
            actions.append({
                "id": "resume_mission", "label": "Continuar", "type": "control", 
                "level": "governed", "icon": "▶️"
            })
            
        # 3. Defensive Actions (Always visible for non-terminal)
        if m.status not in [MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.ARCHIVED]:
            actions.append({
                "id": "abort_mission", "label": "Abortar", "type": "emergency", 
                "level": "danger", "requires_confirmation": True, "requires_pin": True, "icon": "🛑"
            })
            
        return actions

    def get_global_snapshot(self) -> List[Dict[str, Any]]:
        """
        CAPA 1 & 2: Aggregates current governance state across all active/recent missions.
        """
        missions = mission_manager.get_parallel_running_missions()
        completed = mission_manager.get_completed_recent_missions(limit=5)
        missions.extend(completed)
        
        if not missions:
             return []
        
        snapshot = []
        for m in missions:
            # Determine Governance State
            gov_state = "NOMINAL"
            urgency = 1
            
            # Check for hard limits or blocks
            is_blocked = m.status == MissionStatus.BLOCKED
            has_hard_limit = any("CONSTITUTIONAL LIMIT" in r or "LÍMITE CONSTITUCIONAL" in r for r in m.blocked_reasons)
            
            if has_hard_limit:
                gov_state = "HARD_LIMIT_TRIPPED"
                urgency = 5
            elif is_blocked:
                gov_state = "LOCKED"
                urgency = 4
                
            # Authority Session check
            auth_info = m.authority_session or {}
            auth_active = False
            expires_at = auth_info.get("authority_expires_at")
            
            if auth_info.get("authority_granted"):
                if expires_at:
                    try:
                        exp_dt = datetime.fromisoformat(expires_at)
                        if exp_dt > datetime.now():
                            auth_active = True
                            if gov_state == "NOMINAL":
                                gov_state = "OVERRIDDEN" # Privilege active
                                if urgency < 3: urgency = 3
                        else:
                            gov_state = "SESSION_EXPIRED"
                            if urgency < 2: urgency = 2
                    except: pass
            
            # Latest significant event
            events = mission_telemetry.get_recent_events(m.mission_id, limit=10)
            security_events = [e for e in events if e.event_type in [
                "manual_authority_injected", "authority_session_expired", 
                "constitutional_limit_tripped", "mission_blocked"
            ]]
            
            latest_event = None
            if security_events:
                e = security_events[0]
                latest_event = {
                    "type": e.event_type,
                    "msg": e.message,
                    "ts": e.timestamp.strftime("%H:%M")
                }

            snapshot.append({
                "mission_id": m.mission_id,
                "name": m.active_goal[:50] + "..." if len(m.active_goal) > 50 else m.active_goal,
                "status": m.status.value,
                "governance_state": gov_state,
                "urgency": urgency,
                "authority": {
                    "active": auth_active,
                    "expires_at": expires_at
                },
                "latest_event": latest_event,
                "quick_actions": self._get_quick_actions(m),
                "affected_surface": m.related_targets if hasattr(m, 'related_targets') else []
            })
            
        # Sort by urgency DESC, then by name
        snapshot.sort(key=lambda x: (-x["urgency"], x["name"]))
        return snapshot

    def get_hud_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        CAPA 1 (PHASE 84): COGNITIVE OVERLAY HUD SNAPSHOT.
        Aggregates persistent mission context, accepted debt, and critical alerts for the always-on HUD.
        """
        active_mission: Optional[MissionState] = mission_manager.get_active_mission()
        if not active_mission:
            return None
        
        # 0. Global Governance Context (Accepted Debt)
        # CAPA 1-2 (Phase 107): Debt Integration
        from backend.core.ai_host.memory.branch_manager import branch_manager
        debt_data = branch_manager.get_accepted_debt_dashboard()
        debt_summary = debt_data.get("summary", {})
        
        # Determine HUD Severity for Debt
        debt_severity = "NOMINAL"
        if debt_summary.get("overdue_count", 0) > 0 or debt_summary.get("degraded_count", 0) > 0:
             debt_severity = "CRITICAL"
        elif debt_summary.get("review_due_count", 0) > 0:
             debt_severity = "WARNING"
        elif debt_summary.get("total_active_debt", 0) > 0:
             debt_severity = "ACTIVE"

        # 1. Mission Context
        snap = {
            "mission_id": active_mission.mission_id,
            "mission_name": active_mission.active_goal[:40] + ("..." if len(active_mission.active_goal) > 40 else ""),
            "status": active_mission.status.value,
            "debt": {
                "severity": debt_severity,
                "total": debt_summary.get("total_active_debt", 0),
                "urgent_count": debt_summary.get("overdue_count", 0) + debt_summary.get("degraded_count", 0),
                "review_due": debt_summary.get("review_due_count", 0),
                "is_running_under_debt": any(alert["target"] == active_mission.mission_id for alert in debt_summary.get("intervention_required", []))
            }
        }
        
        # 2. Drift & Health (Reusing state from context_snap)
        drift_alerts = active_mission.context_snap.get("drift_alerts", [])
        latest_drift = drift_alerts[-1] if drift_alerts else None
        
        snap["drift"] = {
            "state": latest_drift["severity"] if latest_drift else "NOMINAL",
            "message": latest_drift["message"] if latest_drift else "Alineación Correcta",
            "is_healing": active_mission.context_snap.get("is_healing", False)
        }
        
        # 3. Governance & Authority
        full_snap = self.get_global_snapshot()
        active_gov = next((m for m in full_snap if m["mission_id"] == active_mission.mission_id), None)
        
        if active_gov:
            snap["governance"] = {
                "state": active_gov["governance_state"],
                "urgency": active_gov["urgency"],
                "authority_active": active_gov["authority"]["active"],
                "expires_at": active_gov["authority"]["expires_at"]
            }
        
        # 4. Critical Alert Aggregation (Other missions)
        other_alerts = [m for m in full_snap if m["mission_id"] != active_mission.mission_id and (m["urgency"] >= 4 or m["status"] == "BLOCKED")]
        snap["critical_alerts_count"] = len(other_alerts)
        
        return snap

governance_dashboard = GovernanceDashboard()
