import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.resource_lock_manager import resource_lock_manager
from backend.core.ai_host.memory.mission_telemetry import mission_telemetry
from backend.core.ai_host.memory.priority_engine import priority_engine
from backend.core.ai_host.memory.mission_summarizer import mission_summarizer

logger = logging.getLogger(__name__)

class StrategicLearningEngine:
    """
    CAPA 1 & 2 (PHASE 67): CROSS-MISSION STRATEGIC EVOLUTION.
    Aggregates success data from all missions to improve future rescue suggestions.
    """
    def __init__(self):
        self._init_storage()

    def _init_storage(self):
        with db_manager.get_connection(internal=True) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS mission_learning (
                pattern_key TEXT PRIMARY KEY,
                successful_action TEXT,
                total_roi REAL DEFAULT 0,
                execution_count INTEGER DEFAULT 0,
                confidence REAL DEFAULT 0,
                last_seen TIMESTAMP
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS mission_strategic_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_mission_id TEXT,
                knowledge_type TEXT, -- 'RISK', 'TACTIC_SUCCESS', 'TACTIC_FAILURE', 'DRIFT_PATTERN'
                layer_context TEXT,
                summary TEXT,
                evidence TEXT,
                confidence REAL,
                created_at TIMESTAMP
            )
            """)
            conn.commit()

    def record_strategic_lesson(self, mission_id: str, k_type: str, layer: str, summary: str, evidence: str = "", conf: float = 0.5):
        """
        CAPA 1, 2 & 3 (PHASE 78): GLOBAL KNOWLEDGE PERSISTENCE.
        Stores a distilled strategic lesson for the entire ecosystem.
        """
        with db_manager.get_connection(internal=True) as conn:
            conn.execute("""
                INSERT INTO mission_strategic_knowledge (source_mission_id, knowledge_type, layer_context, summary, evidence, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (mission_id, k_type, layer, summary, evidence, conf))
            conn.commit()
        logger.info(f"[STRATEGIC_LEARNING] Global Knowledge Item recorded: {k_type} for {layer}")

    def get_global_wisdom(self, layer: str) -> List[Dict[str, Any]]:
        """
        Retrieves all relevant strategic lessons for a specific layer.
        """
        with db_manager.get_connection(internal=True) as conn:
            cursor = conn.execute("""
                SELECT knowledge_type, summary, confidence, source_mission_id, layer_context 
                FROM mission_strategic_knowledge 
                WHERE layer_context LIKE ? OR layer_context = 'global'
                ORDER BY created_at DESC LIMIT 5
            """, (f"%{layer}%",))
            rows = cursor.fetchall()
            
        return [
            {
                "type": r[0],
                "summary": r[1],
                "confidence": r[2],
                "source": r[3],
                "context": r[4]
            } for r in rows
        ]

    def record_rescue_success(self, context_key: str, action_type: str, roi: float):
        """
        Records a successful rescue. Context key handles layer/drift patterns.
        """
        pk = f"{context_key}::{action_type}"
        with db_manager.get_connection(internal=True) as conn:
            conn.execute("""
            INSERT INTO mission_learning (pattern_key, successful_action, total_roi, execution_count, last_seen)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(pattern_key) DO UPDATE SET
                total_roi = total_roi + excluded.total_roi,
                execution_count = execution_count + 1,
                confidence = MIN(1.0, (total_roi + excluded.total_roi) / (100.0 * (execution_count + 1))), -- Normalizing to [0, 1]
                last_seen = CURRENT_TIMESTAMP
            """, (pk, action_type, roi))
            conn.commit()
        logger.info(f"[STRATEGIC_LEARNING] Pattern recorded: {pk} | ROI: {roi}")

    def get_contextual_intelligence(self, context_key: str) -> List[Dict[str, Any]]:
        """
        Retrieves historical knowledge for a specific drift context.
        """
        prefix = f"{context_key}::%"
        with db_manager.get_connection(internal=True) as conn:
            cursor = conn.execute("""
                SELECT successful_action, confidence, execution_count, 
                       (total_roi / execution_count) as avg_roi 
                FROM mission_learning WHERE pattern_key LIKE ? 
                ORDER BY confidence DESC LIMIT 3
            """, (prefix,))
            rows = cursor.fetchall()
        
        return [
            {
                "action": r[0],
                "confidence": r[1],
                "cases": r[2],
                "avg_roi": r[3]
            } for r in rows
        ]

    def record_rescue_failure(self, context_key: str, action_type: str, penalty_weight: float = 0.5):
        """
        CAPA 1 & 2 (PHASE 75): COGNITIVE HEALING / NEGATIVE LEARNING.
        Penalizes tactical confidence when an action is reversed or fails.
        """
        pk = f"{context_key}::{action_type}"
        print(f"DEBUG: [STRATEGIC_LEARNING] record_rescue_failure for PK: {pk}")
        from datetime import datetime
        with db_manager.get_connection(internal=True) as conn:
            # 1. Fetch current trust
            cursor = conn.execute("SELECT total_roi, execution_count, confidence FROM mission_learning WHERE pattern_key = ?", (pk,))
            row = cursor.fetchone()
            
            if row:
                total_r, count, conf = row
                print(f"       DEBUG: Found row. Current Conf: {conf}")
                # We subtract penalty from ROI to lower the average
                new_roi = max(0, total_r - 50.0)
                # Confidence drop is more aggressive: -20% per failure
                new_conf = max(0.05, conf * 0.8)
                if new_conf > 1.0: new_conf = new_conf / 100.0 # Migration fix if old data exists
                
                print(f"       DEBUG: New Conf to save: {new_conf}")
                
                conn.execute("""
                    UPDATE mission_learning 
                    SET total_roi = ?, confidence = ?, last_seen = ? 
                    WHERE pattern_key = ?
                """, (new_roi, new_conf, datetime.now().isoformat(), pk))
                logger.warning(f"[STRATEGIC_LEARNING] Pattern penalised: {pk} | New Conf: {new_conf:.2f}")
            else:
                print(f"       DEBUG: No row found for PK: {pk}")
                # If it's a new failure (never succeeded), record with low initial confidence
                conn.execute("""
                    INSERT INTO mission_learning (pattern_key, successful_action, total_roi, execution_count, confidence, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pk, action_type, 0.0, 1, 0.05, datetime.now().isoformat()))
                logger.info(f"[STRATEGIC_LEARNING] New failure recorded: {pk}")
            
            conn.commit()

    def get_preventive_wisdom(self, layer: str) -> List[Dict[str, Any]]:
        """
        CAPA 1 (PHASE 70): PRE-MISSION PREVENTIVE WISDOM.
        Retrieves high-impact lessons learned in a similar technical layer.
        """
        prefix = f"{layer}:%"
        with db_manager.get_connection(internal=True) as conn:
            cursor = conn.execute("""
                SELECT pattern_key, successful_action, (total_roi / execution_count) as avg_roi, confidence, execution_count
                FROM mission_learning 
                WHERE pattern_key LIKE ? 
                ORDER BY avg_roi DESC, execution_count DESC LIMIT 2
            """, (prefix,))
            rows = cursor.fetchall()
            
        return [
            {
                "pattern": r[0].split('::')[0],
                "best_tactic": r[1],
                "expected_impact": r[2],
                "confidence": r[3],
                "cases": r[4]
            } for r in rows
        ]

from .mission_models import MissionStatus, MissionState, MissionHandoff, MissionCompactDigest

class MissionManager:
    """
    Surgical Layer for Mission Memory Persistence.
    Ensures OmniWeb never forgets its technical goals.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MissionManager, cls).__new__(cls)
            cls._instance.active_mission = None
            cls._instance.learning_engine = StrategicLearningEngine()
            cls._instance.rehydrate_active_mission()
        return cls._instance

    def rehydrate_active_mission(self):
        """
        CAPA 2 (PHASE 80): DEEP STRATEGIC RECOVERY HOOK.
        Restores focus and generates an initial recovery path.
        """
        logger.info("[MISSION_MANAGER] Initiating cold rehydration of mission focus...")
        try:
            m = self.get_active_mission()
            if m:
                logger.info(f"[MISSION_MANAGER] Focus restored: {m.mission_id} - {m.active_goal}")
                # PHASE 80: Generate Recovery Strategy immediately
                recovery = m.generate_deep_recovery_plan()
                m.last_recovery = recovery # Transient storage
                
                # Execute Auto-Recovery if policy allows
                if recovery.get("is_auto_eligible"):
                     auto_result = m.execute_recovery_auto_action(recovery)
                     if auto_result.get("success"):
                          recovery["policy_decision"]["auto_executed"] = True
                          recovery["policy_decision"]["execution_details"] = auto_result
                          logger.info(f"[MISSION_MANAGER] Safe Auto-Recovery executed: {auto_result['action_executed']}")

                # Telemetry
                mission_telemetry.record_event(
                    m.mission_id, "mission_rehydrated", 
                    f"Misión recuperada con estrategia: {recovery['recovery_status']}", 
                    details=recovery,
                    source_actor="MissionManager"
                )
                logger.info(f"[MISSION_MANAGER] Strategic Recovery synthesized: {recovery['recovery_status']}")
            else:
                logger.debug("[MISSION_MANAGER] No active missions found to rehydrate.")
        except Exception as e:
            logger.error(f"[MISSION_MANAGER] Critical Failure during focus rehydration: {e}")

    def create_mission(self, goal: str, plan_id: str = None, pending_steps: List[str] = None, plan: Optional[Any] = None) -> MissionState:
        print(f"DEBUG: [MISSION_MANAGER] create_mission called for goal: '{goal}'")
        """
        Initializes a new mission and persists it.
        """
        snap = {}
        if plan:
            # Serializamos el plan para persistencia si es un objeto TaskPlan o ExecutionTree
            plan_json = {}
            if hasattr(plan, 'model_dump'):
                plan_json = plan.model_dump(mode='json')
            elif hasattr(plan, 'to_dict'):
                plan_json = plan.to_dict()
            else:
                plan_json = str(plan)
            
            snap["tree"] = plan_json
            snap["plan_data"] = plan_json # Legacy compatibility

        mission = MissionState(
            active_goal=goal,
            plan_id=plan_id,
            pending_steps=pending_steps or [],
            context_snap=snap
        )
        self.save_mission(mission)
        self.active_mission = mission
        logger.info(f"[MISSION_MANAGER] New Mission Created: {mission.mission_id} - {goal}")
        
        # Phase: MISSION CRITICAL TELEMETRY
        mission_telemetry.record_event(
            mission.mission_id, "mission_started", 
            f"Nueva misión iniciada: {goal}", 
            details={"plan_id": plan_id},
            source_actor="MissionManager"
        )
        
        # Phase: MISSION CONFLICT RESOLVER - Early Conflict Check
        if plan:
            targets = []
            if hasattr(plan, 'affected_layers'): targets.extend(plan.affected_layers)
            
            conflict = resource_lock_manager.check_conflict(targets, mission.mission_id)
            if conflict:
                mission.status = MissionStatus.BLOCKED
                msg = f"CONFLICT: Module/Layer '{conflict['resource_key']}' locked by mission {conflict['mission_id']}"
                mission.blocked_reasons.append(msg)
                self.save_mission(mission)
                logger.warning(f"[MISSION_MANAGER] Mission {mission.mission_id} BLOCKED by early conflict check.")
                
                # Telemetry
                mission_telemetry.record_event(
                    mission.mission_id, "resource_conflict", 
                    f"Bloqueo por conflicto de recurso: {conflict['resource_key']}", 
                    severity="WARNING", 
                    details=conflict,
                    source_actor="MissionManager"
                )
        
        return mission

    def get_active_mission(self) -> Optional[MissionState]:
        """Returns the currently focused mission."""
        return self.active_mission

    def create_sub_mission(self, parent_id: str, goal: str, relation_type: str = "SUB_MISSION", inherit_context: bool = True) -> MissionState:
        """
        Creates a child mission linked to a parent.
        """
        parent = self.get_mission_by_id(parent_id)
        if not parent:
            logger.error(f"[MISSION_MANAGER] Cannot create sub-mission: Parent {parent_id} not found.")
            return None
        
        snap = {}
        if inherit_context:
            snap = parent.context_snap.copy()
            # Basic inheritance: related targets and parameters
        
        sub = MissionState(
            active_goal=goal,
            parent_id=parent_id,
            relation_type=relation_type,
            related_targets=parent.related_targets.copy(),
            parameters=parent.parameters.copy(),
            context_snap=snap
        )
        
        # Update parent
        if sub.mission_id not in parent.child_ids:
            parent.child_ids.append(sub.mission_id)
            self.save_mission(parent)
        
        # Save sub
        self.save_mission(sub)
        self.active_mission = sub
        logger.info(f"[MISSION_MANAGER] Sub-mission created: {sub.mission_id} (Parent: {parent_id})")
        return sub

    def add_dependency(self, mission_id: str, dependency_id: str):
        """
        Adds a pre-condition dependency.
        """
        mission = self.get_mission_by_id(mission_id)
        if not mission: return
        
        if dependency_id not in mission.dependency_ids:
            mission.dependency_ids.append(dependency_id)
            
            # Check if current status should be BLOCKED if dependency is not COMPLETED
            dep = self.get_mission_by_id(dependency_id)
            if dep and dep.status != MissionStatus.COMPLETED:
                mission.status = MissionStatus.BLOCKED
                mission.blocked_reasons.append(f"DEPENDENCY_MISSING: Waiting for {dependency_id}")
            
            self.save_mission(mission)
            logger.info(f"[MISSION_MANAGER] Dependency added: {mission_id} -> {dependency_id}")

    def get_drift_alerts(self) -> List[Dict[str, Any]]:
        """
        CAPA 2 (PHASE 64): PROACTIVE COGNITIVE ALERTS.
        Identifies missions that crossed drift thresholds and need tactical notification.
        """
        logger.info("[MISSION_MANAGER] Checking for pending drift alerts...")
        # Only check missions in relevant states (IN_FLIGHT)
        with db_manager.get_connection() as conn:
             rows = conn.execute("SELECT mission_id FROM system_missions WHERE status IN ('OPEN', 'RUNNING', 'BLOCKED', 'PAUSED')").fetchall()
             active_ids = [row["mission_id"] for row in rows]
        
        alerts = []
        for m_id in active_ids:
             m = self.get_mission(m_id)
             if not m or not m.multimodal_history: continue
             
             report = m.analyze_cognitive_drift()
             current_class = report["status"]
             last_alerted = m.parameters.get("last_alerted_drift", "ALIGNED")
             
             # Trigger logic: State became worse or is already CRITICAL but increased score
             should_alert = False
             severity = "INFO"
             
             if current_class == "CRITICAL_DRIFT" and last_alerted != "CRITICAL_DRIFT":
                  should_alert = True
                  severity = "CRITICAL"
             elif current_class == "DRIFT_WARNING" and last_alerted not in ["DRIFT_WARNING", "CRITICAL_DRIFT"]:
                  should_alert = True
                  severity = "WARNING"
             elif current_class == "ATTENTION_REQUIRED" and last_alerted not in ["ATTENTION_REQUIRED", "DRIFT_WARNING", "CRITICAL_DRIFT"]:
                  # Only alert attention if first time
                  should_alert = True
                  severity = "ATTENTION"
                  
             if should_alert:
                  alerts.append({
                      "mission_id": m.mission_id,
                      "goal": m.active_goal,
                      "drift_class": current_class,
                      "drift_score": report["drift_score"],
                      "reason": report["reasons"][0] if report["reasons"] else "Desviación técnica detectada.",
                      "severity": severity,
                      "timestamp": datetime.now().isoformat()
                  })
                  # Persist state to prevent spam
                  m.parameters["last_alerted_drift"] = current_class
                  self.save_mission(m)
                  
        return alerts

    def get_portfolio_cognitive_health(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        CAPA 2 (PHASE 82): REAL-TIME AGGREGATION ENGINE.
        Consolidates the alignment state of all active or recent missions with live precision.
        """
        logger.info("[MISSION_MANAGER] Aggregating live portfolio cognitive health...")
        # Get all recent missions
        m_ids = []
        with db_manager.get_connection() as conn:
             rows = conn.execute("SELECT mission_id FROM system_missions ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
             m_ids = [row["mission_id"] for row in rows]
        
        health_list = []
        for m_id in m_ids:
             m = self.get_mission(m_id)
             if not m:
                  continue
             
             snapshot = m.get_live_drift_snapshot()
             health_list.append(snapshot)
             
        # Prioritize by urgency_rank and drift_score
        return sorted(health_list, key=lambda x: (x["urgency_rank"], x["drift_score"]), reverse=True)

    def get_mission(self, mission_id: str) -> Optional[MissionState]:
        """Fetches any mission from DB by ID."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Ensure the chip has permission to read missions
                from backend.core.permissions import enforce_permission
                try: enforce_permission("db_access")
                except: pass

                row = conn.execute("SELECT * FROM system_missions WHERE mission_id = ?", (mission_id,)).fetchone()
                if row:
                    return self._row_to_mission(row)
        return None

    def get_mission_by_id(self, mission_id: str) -> Optional[MissionState]:
        """Fetches any mission from DB by ID."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Ensure the chip has permission to read missions
                from backend.core.permissions import enforce_permission
                try: enforce_permission("db_access")
                except: pass

                row = conn.execute("SELECT * FROM system_missions WHERE mission_id = ?", (mission_id,)).fetchone()
                if row:
                    return self._row_to_mission(row)
        return None

    def get_sub_missions(self, parent_id: str) -> List[MissionState]:
        """Retrieves all sub-missions of a given parent."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM system_missions WHERE parent_id = ?", (parent_id,)).fetchall()
                return [self._row_to_mission(row) for row in rows]

    def reevaluate_dependents(self, completed_id: str):
        """
        Unblocks missions that were waiting for this one.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Find missions that have this ID in their dependency_ids
                # In SQLite, we search for it in the JSON string
                rows = conn.execute("SELECT * FROM system_missions WHERE dependency_ids LIKE ?", (f'%"{completed_id}"%',)).fetchall()
                for row in rows:
                    mission = self._row_to_mission(row)
                    # Check if ALL dependencies are now COMPLETED
                    all_ready = True
                    for dep_id in mission.dependency_ids:
                        dep = self.get_mission_by_id(dep_id)
                        if not dep or dep.status != MissionStatus.COMPLETED:
                            all_ready = False
                            break
                    
                    if all_ready and mission.status == MissionStatus.BLOCKED:
                        mission.status = MissionStatus.OPEN
                        # Clean up the specific blocked reason
                        mission.blocked_reasons = [r for r in mission.blocked_reasons if "DEPENDENCY_MISSING" not in r]
                        self.save_mission(mission)
                        logger.info(f"[MISSION_MANAGER] Mission {mission.mission_id} UNBLOCKED by completion of {completed_id}")

    def rollback_branch(self, mission_id: str, reason: str = "Rollback triggered by Creator"):
        """
        Recursively marks a mission and all its children as ROLLED_BACK.
        Surgically removes the branch from active flow.
        """
        mission = self.get_mission_by_id(mission_id)
        if not mission: return
        
        # 1. Recursive rollback of children
        for child_id in mission.child_ids:
            self.rollback_branch(child_id, reason=f"Parent rollback: {mission_id}")
            
        # 2. Update status of current mission
        mission.status = MissionStatus.ROLLED_BACK
        mission.blocked_reasons.append(f"ROLLBACK: {reason}")
        self.save_mission(mission)
        
        # 3. If it was active, clear it
        logger.warning(f"[MISSION_MANAGER] Branch {mission_id} rolled back.")
        
        # Telemetry
        mission_telemetry.record_event(
            mission_id, "rollback_branch", 
            f"Rama de misión revertida: {reason}", 
            severity="WARNING",
            source_actor="MissionManager"
        )

    def archive_mission_branch(self, mission_id: str):
        """Marks a branch as ARCHIVED (hidden but preserved)."""
        mission = self.get_mission_by_id(mission_id)
        if not mission: return
        
        for child_id in mission.child_ids:
            self.archive_mission_branch(child_id)
            
        mission.status = MissionStatus.ARCHIVED
        self.save_mission(mission)
        logger.info(f"[MISSION_MANAGER] Branch {mission_id} archived.")

    def clone_mission_for_retry(self, mission_id: str, new_goal: str = None, relation_type: str = "RETRY") -> Optional[MissionState]:
        """
        Clones a mission (e.g. a failed one) to start a new branch/retry.
        Preserves parent, dependencies and config, but creates a new identity.
        """
        original = self.get_mission_by_id(mission_id)
        if not original: return None
        
        # 1. Create new state
        new_state = MissionState(
            active_goal=new_goal or original.active_goal,
            parent_id=original.parent_id,
            relation_type=relation_type,
            related_targets=original.related_targets.copy(),
            parameters=original.parameters.copy(),
            context_snap=original.context_snap.copy(),
            dependency_ids=original.dependency_ids.copy(),
            retried_from=mission_id
        )
        
        # 2. Link in parent if exists
        if original.parent_id:
            parent = self.get_mission_by_id(original.parent_id)
            if parent:
                parent.child_ids.append(new_state.mission_id)
                self.save_mission(parent)
        
        # 3. Mark original as SUPERSEDED (optional but recommended for clarity)
        original.status = MissionStatus.SUPERSEDED
        original.blocked_reasons.append(f"Superseded by retry: {new_state.mission_id}")
        self.save_mission(original)
        
        # 4. Save and set active
        self.save_mission(new_state)
        self.active_mission = new_state
        
        logger.info(f"[MISSION_MANAGER] Mission {mission_id} retried as {new_state.mission_id}")
        return new_state

    def switch_focus(self, mission_id: str):
        """
        Changes the global focus to a specific mission.
        Keeps others in OPEN or RUNNING state.
        """
        target = self.get_mission_by_id(mission_id)
        if not target: return
        
        # 1. Update timestamp for focus stack
        target.last_focused_at = datetime.now()
        
        # 2. If it was BLOCKED, it stays BLOCKED but now it is the 'active_mission' 
        # for inspection.
        # If it was OPEN, it stays OPEN (or RUNNING if we want background activity).
        self.save_mission(target)
        self.active_mission = target
        
        logger.info(f"[MISSION_MANAGER] Focus switched to: {mission_id} - {target.active_goal}")
        return target

    def get_parallel_running_missions(self) -> List[MissionState]:
        """
        Returns missions currently in RUNNING or BLOCKED status.
        These are tasks OmniWeb considers 'in-flight' or waiting.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM system_missions WHERE status IN ('RUNNING', 'BLOCKED', 'OPEN', 'PAUSED')").fetchall()
                raw_missions = [self._row_to_mission(row) for row in rows]
                # Rank them before returning
                return priority_engine.rank_portfolio(raw_missions, focal_id=(self.active_mission.mission_id if self.active_mission else None))

    def get_archived_missions(self, limit: int = 20) -> List[MissionState]:
        """Returns missions marked as ARCHIVED, ROLLED_BACK, SUPERSEDED or FAILED."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM system_missions WHERE status IN ('ARCHIVED', 'ROLLED_BACK', 'SUPERSEDED', 'FAILED') ORDER BY updated_at DESC LIMIT ?", 
                    (limit,)
                ).fetchall()
                return [self._row_to_mission(row) for row in rows]

    def get_completed_recent_missions(self, limit: int = 10) -> List[MissionState]:
        """Returns recently completed missions."""
        _ = self  # Keep reference
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM system_missions WHERE status = 'COMPLETED' ORDER BY updated_at DESC LIMIT ?", 
                    (limit,)
                ).fetchall()
                return [self._row_to_mission(row) for row in rows]

    def save_mission(self, mission: MissionState):
        """
        Persists mission state to SQLite.
        """
        # PHASE 21: Auto-inject core health synthesis
        try:
            from backend.core.ai_host.shadow_swarm.approval_gate import approval_gate
            mission.context_snap["governance_health"] = approval_gate.get_governance_health(mission)
        except Exception as e:
            logger.warning(f"[MISSION_MANAGER] Could not inject governance health: {e}")

        # PHASE 53: Auto-generate compact digest
        try:
            mission.compact_digest = mission_summarizer.create_compact_digest(mission)
        except Exception as e:
            logger.warning(f"[MISSION_MANAGER] Failed to create compact digest: {e}")

        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                query = """
                INSERT OR REPLACE INTO system_missions (
                    mission_id, active_goal, status, plan_id, 
                    completed_steps, pending_steps, blocked_reasons, 
                    related_targets, parameters, context_snap, visual_context, multimodal_history, 
                    parent_id, child_ids, dependency_ids, relation_type, 
                    retried_from, branched_from, last_focused_at, updated_at,
                    priority_score, priority_class, readiness_state, compact_digest
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Robust serialization
                v_ctx = json.dumps(mission.visual_context) if mission.visual_context else None
                m_hist = json.dumps(mission.multimodal_history) if mission.multimodal_history else "[]"
                params = json.dumps(mission.parameters) if mission.parameters else "{}"
                snap = json.dumps(mission.context_snap) if mission.context_snap else "{}"

                conn.execute(query, (
                    mission.mission_id,
                    mission.active_goal,
                    mission.status.value,
                    mission.plan_id,
                    json.dumps(mission.completed_steps),
                    json.dumps(mission.pending_steps),
                    json.dumps(mission.blocked_reasons),
                    json.dumps(mission.related_targets),
                    params,
                    snap,
                    v_ctx,
                    m_hist,
                    mission.parent_id,
                    json.dumps(mission.child_ids),
                    json.dumps(mission.dependency_ids),
                    mission.relation_type,
                    mission.retried_from,
                    mission.branched_from,
                    mission.last_focused_at.isoformat() if isinstance(mission.last_focused_at, datetime) else mission.last_focused_at,
                    datetime.now().isoformat(),
                    mission.priority_score,
                    mission.priority_class,
                    mission.readiness_state,
                    mission.compact_digest.model_dump_json() if mission.compact_digest else None
                ))
                conn.commit()

    def record_step_progress(self, mission_id: str, step_id: str, status: str, message: str = None):
        """Records telemetry for a specific step execution."""
        mission = self.get_mission_by_id(mission_id)
        if not mission: return
        
        event_type = f"step_{status.lower()}"
        severity = "INFO"
        if status == "FAILED": severity = "ERROR"
        
        mission_telemetry.record_event(
            mission_id, event_type, 
            message or f"Paso {step_id}: {status}", 
            severity=severity, 
            step_id=step_id,
            source_actor="MissionManager"
        )

    def get_active_mission(self) -> Optional[MissionState]:
        
        if self.active_mission and self.active_mission.status in [MissionStatus.OPEN, MissionStatus.PAUSED]:
            return self.active_mission

        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    row = conn.execute(
                        "SELECT * FROM system_missions WHERE status IN ('OPEN', 'PAUSED') ORDER BY updated_at DESC LIMIT 1"
                    ).fetchone()
                    
                    if row:
                        mission = self._row_to_mission(row)
                        self.active_mission = mission
                        return mission
            except Exception as e:
                logger.error(f"[MISSION_MANAGER] Error loading active mission: {e}")
        return None

    def propagate_roadmap(self, mission_id: str, jobs: List[Any]):
        """
        Initializes the execution tree with the full swarm roadmap.
        Ensures the roadmap survives restarts even before execution begins.
        """
        mission = self.get_active_mission()
        if not mission or mission.mission_id != mission_id: return

        if not mission.context_snap.get("tree"):
            mission.context_snap["tree"] = {
                "root": {"id": "root", "label": mission.active_goal, "status": "ACTIVE", "children": []}
            }
        
        tree = mission.context_snap["tree"]
        existing_ids = self._get_all_node_ids(tree["root"])
        
        for job in jobs:
            # We assume job has 'id' and 'description' (ShadowJob duck-typing)
            jid = getattr(job, 'id', str(job.get('id', '')))
            if not jid: continue
            
            if jid not in existing_ids:
                new_node = {
                    "id": jid,
                    "label": getattr(job, 'description', job.get('description', 'Shadow Task')),
                    "status": "PENDING",
                    "evidence": None,
                    "children": []
                }
                tree["root"]["children"].append(new_node)
        
        self.save_mission(mission)
        logger.info(f"[MISSION_MANAGER] Roadmap propagated for mission {mission_id} ({len(jobs)} jobs).")

    def _get_all_node_ids(self, node: Dict[str, Any]) -> List[str]:
        ids = [str(node.get("id"))]
        for child in node.get("children", []):
            ids.extend(self._get_all_node_ids(child))
        return ids

    def update_step_status(self, step_id: Any, status: str, message: str = None, evidence: str = None, deep_evidence: Any = None, save: bool = True, source_actor: str = "system"):
        mission = self.get_active_mission()
        if not mission: return

        target_id = None
        if isinstance(step_id, str) and step_id.startswith("plan_job_"):
            try: target_id = int(step_id.replace("plan_job_", ""))
            except: target_id = step_id
        else:
            target_id = step_id

        # 1. Update Persistent Lists
        str_id = str(target_id)
        if status == "COMPLETED":
            if str_id in mission.pending_steps:
                mission.pending_steps.remove(str_id)
            if str_id not in mission.completed_steps:
                mission.completed_steps.append(str_id)
        elif status == "FAILED":
            if str_id not in mission.blocked_reasons:
                mission.blocked_reasons.append(f"Step {str_id} failed.")

        # 2. Update Execution Tree (Recursive Search)
        tree = mission.context_snap.get("tree")
        if tree and "root" in tree:
            self._update_node_in_tree(tree["root"], target_id, status, evidence, deep_evidence)
            mission.context_snap["tree"] = tree # Re-sync

        # 3. Telemetry Event & Snap (Phase: GOVERNANCE & AUDIT OVERLAY)
        event_text = message or f"Paso {target_id}: {status}"
        
        # Persistent Telemetry
        mission_telemetry.record_event(
            mission.mission_id, 
            f"step_{status.lower()}", 
            event_text,
            severity="ERROR" if status == "FAILED" else ("WARNING" if status == "NEEDS_REVIEW" else "INFO"),
            step_id=str(target_id),
            details={"evidence": evidence, "actor": source_actor},
            source_actor=source_actor
        )

        mission.telemetry_snap = {
            "last_event": event_text,
            "last_sync": datetime.now().strftime("%H:%M:%S"),
            "status_color": self._get_status_color(status),
            "current_evidence": evidence or (deep_evidence.get('summary') if deep_evidence and isinstance(deep_evidence, dict) else (deep_evidence.get('explanation') if isinstance(deep_evidence, dict) else None))
        }

        # 4. Global Goal Completion
        if not mission.pending_steps and status == "COMPLETED":
             mission.status = MissionStatus.COMPLETED

        mission.updated_at = datetime.now()
        if save:
            self.save_mission(mission)
            logger.info(f"[MISSION_MANAGER] Step {target_id} -> {status} [Actor: {source_actor}]")
        else:
            logger.debug(f"[MISSION_MANAGER] Step {target_id} updated in-memory only.")

    def create_checkpoint(self, mission_id: str, label: str, targets: List[str] = []):
        """
        Creates a system-wide checkpoint.
        """
        from .checkpoint_engine import checkpoint_engine
        checkpoint_id = checkpoint_engine.create_snapshot(mission_id, label, targets)
        
        # Register in mission context for UI
        mission = self.get_active_mission()
        if mission:
             checkpoints = mission.context_snap.get("checkpoints", [])
             checkpoints.append({
                 "id": checkpoint_id,
                 "label": label,
                 "timestamp": datetime.now().isoformat()
             })
             mission.context_snap["checkpoints"] = checkpoints
             self.save_mission(mission)
        return checkpoint_id

    def rollback_mission(self, mission_id: str, checkpoint_id: str):
        """
        Rolls back the mission to a previous state.
        """
        from .checkpoint_engine import checkpoint_engine
        checkpoint_engine.rollback(mission_id, checkpoint_id)
        
        # RELOAD MISSION FROM DB (The DB just changed!)
        self._active_mission = None # Clear memory cache
        logger.warning(f"[MISSION_MANAGER] Mission {mission_id} rolled back to {checkpoint_id} and memory rehydrated.")
        return True

    def _update_node_in_tree(self, node: Dict[str, Any], target_id: Any, status: str, evidence: str = None, deep_evidence: Dict[str, Any] = None):
        if str(node.get("id")) == str(target_id):
            node["status"] = status
            if evidence: node["evidence"] = evidence
            if deep_evidence: node["deep_evidence"] = deep_evidence
            return True
        
        for child in node.get("children", []):
            if self._update_node_in_tree(child, target_id, status, evidence, deep_evidence):
                # If a child is active, the parent phase could also show activity (optional enhancement)
                if status == "ACTIVE" and node.get("type") == "phase":
                    node["status"] = "ACTIVE"
                return True
        return False

    def _get_status_color(self, status: str) -> str:
        colors = {
            "ACTIVE": "#0096ff",
            "COMPLETED": "#00ff88",
            "FAILED": "#ff4444",
            "RECOVERING": "#ffcc00",
            "PENDING": "#999",
            "NEEDS_REVIEW": "#ffaa00"
        }
        return colors.get(status, "#fff")

    def update_mission_step(self, completed_step: str):
        """Legacy compatibility wrapper."""
        self.update_step_status(completed_step, "COMPLETED")

    def set_status(self, status: MissionStatus, reason: str = None):
        """
        Updates mission status significantly.
        """
        mission = self.get_active_mission()
        if not mission: return

        if mission.status == status and not reason: return
        mission.status = status
        if reason:
            mission.blocked_reasons.append(reason)
        
        mission.updated_at = datetime.now()
        self.save_mission(mission)
        logger.info(f"[MISSION_MANAGER] Mission {mission.mission_id} status changed to {status.value}")
        
        # Phase: MISSION CONFLICT RESOLVER - Release locks on terminal states
        if status in [MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.ARCHIVED, MissionStatus.ROLLED_BACK]:
            resource_lock_manager.release_all_for_mission(mission.mission_id)

    def update_mission_parameters(self, new_params: Dict[str, Any]):
        """
        Updates the active mission's operational constitution in real-time (Phase 20).
        """
        mission = self.get_active_mission()
        if not mission: return

        history = mission.context_snap.get("parameter_history", [])
        
        # Merge lists (forbidden_paths, etc.) or replace individual flags
        for key, val in new_params.items():
            old_val = mission.parameters.get(key)
            if old_val == val: continue
            
            # Record change
            history.append({
                "timestamp": datetime.now().isoformat(),
                "parameter": key,
                "from": old_val,
                "to": val
            })
            
            # Smart merging for lists
            if isinstance(val, list) and isinstance(old_val, list):
                # If we are adding (not "sacá"), we union. 
                # If the prompt was "sacá X", CommandInterpreter should ideally handle that.
                # For now, we overwrite if interpreted as a new state, or we could union.
                # Let's overwrite for simplicity as the interpreter should return the desired NEW state.
                mission.parameters[key] = val
            else:
                mission.parameters[key] = val

        mission.context_snap["parameter_history"] = history
        mission.updated_at = datetime.now()
        self.save_mission(mission)
        logger.info(f"[MISSION_MANAGER] Mission parameters updated dynamically: {list(new_params.keys())}")

    def save_governance_snapshot(self, name: str, params: Dict[str, Any]) -> str:
        """
        Saves the current mission parameters as a named governance profile (Phase 21).
        """
        snapshot_id = str(uuid.uuid4())
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT INTO system_governance_snapshots (snapshot_id, name, parameters) VALUES (?, ?, ?)",
                    (snapshot_id, name, json.dumps(params))
                )
                conn.commit()
        logger.info(f"[MISSION_MANAGER] Governance snapshot saved: {name} ({snapshot_id})")
        
        # Sync with active mission for UI visibility
        mission = self.get_active_mission()
        if mission:
             profiles = mission.context_snap.get("governance_profiles", [])
             if name not in profiles:
                  profiles.append(name)
             mission.context_snap["governance_profiles"] = profiles
             self.save_mission(mission)
             
        return snapshot_id

    def get_governance_snapshot(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves parameters from a named snapshot.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute(
                    "SELECT parameters FROM system_governance_snapshots WHERE name = ? ORDER BY created_at DESC LIMIT 1",
                    (name,)
                ).fetchone()
                if row:
                    return json.loads(row['parameters'])
        return None

    def list_governance_snapshots(self) -> List[Dict[str, Any]]:
        """
        Lists all available governance snapshots.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT name, created_at FROM system_governance_snapshots ORDER BY created_at DESC").fetchall()
                return [{"name": r['name'], "created_at": r['created_at']} for r in rows]

    def track_risk_consumption(self, amount: float):
        """
        Accumulates operational risk (Phase 21).
        If budget is exceeded, pauses mission and triggers authority block.
        """
        mission = self.get_active_mission()
        if not mission: return

        params = mission.parameters
        budget = params.get("risk_budget", 10.0)
        consumed = params.get("risk_consumed", 0.0)
        
        new_consumed = consumed + amount
        params["risk_consumed"] = round(new_consumed, 2)
        params["risk_budget"] = budget # Ensure it exists

        if new_consumed >= budget and mission.status == MissionStatus.OPEN:
             mission.status = MissionStatus.PAUSED
             mission.blocked_reasons.append(f"PRESUPUESTO DE RIESGO AGOTADO: Consumido {new_consumed}/{budget}")
             logger.warning(f"[MISSION_MANAGER] Autonomy boundary reached. Mission PAUSED for Authority Injection.")

        mission.updated_at = datetime.now()
        self.save_mission(mission)
        logger.debug(f"[MISSION_MANAGER] Risk updated: {params['risk_consumed']}/{budget}")

    def authorize_risk_extension(self, extra_budget: float = 5.0):
        """
        Extends risk budget by authority injection (Phase 21).
        """
        mission = self.get_active_mission()
        if not mission: return

        current_budget = mission.parameters.get("risk_budget", 10.0)
        mission.parameters["risk_budget"] = current_budget + extra_budget
        
        if mission.status == MissionStatus.PAUSED:
             # Resume if it was blocked by risk or stabilization
             mission.status = MissionStatus.OPEN
             logger.info(f"[MISSION_MANAGER] Authority injection received. Mission RESUMED.")
        
        self.save_mission(mission)

    def trigger_cooldown(self):
        """Activates stabilization phase (Phase 21)."""
        mission = self.get_active_mission()
        if not mission or mission.status != MissionStatus.OPEN: return
        
        mission.status = MissionStatus.PAUSED
        mission.parameters["cooldown_active"] = True
        mission.blocked_reasons.append("ENFRIAMIENTO OBLIGATORIO: Verificando estabilidad del sistema tras múltiples mutaciones.")
        
        self.save_mission(mission)
        logger.warning(f"[MISSION_MANAGER] Cooldown triggered. System stabilization in progress.")

    def complete_stabilization(self):
        """Resumes mission after cooldown (Phase 21)."""
        mission = self.get_active_mission()
        if not mission: return
        
        mission.parameters["cooldown_active"] = False
        mission.parameters["consecutive_mutations"] = 0
        
        if mission.status == MissionStatus.PAUSED:
             # Remove stabilization reason
             mission.blocked_reasons = [r for r in mission.blocked_reasons if "ENFRIAMIENTO" not in r]
             if not mission.blocked_reasons:
                 mission.status = MissionStatus.OPEN
        
        self.save_mission(mission)
        logger.info(f"[MISSION_MANAGER] Stabilization complete. Ready for next wave.")

    def get_governance_manual(self) -> str:
        """Generates a synthesized manual of the 15 governance blocks implemented (Phase 21)."""
        return """
# OMNIWEB: MANUAL DE GOBERNANZA TOTAL (SÍNTESIS V1.0)

Este documento resume los mecanismos de control que protegen la arquitectura de OmniWeb.

## I. CONTROL CONSTITUCIONAL
1. **Natural Mission Intake**: Traducción de lenguaje humano a directivas de misión.
2. **Rich Constraint Mapping**: Mapeo granular de lo que la IA NO debe tocar.
3. **Constitución Dinámica**: Capacidad de alterar reglas en caliente sin reiniciar.
4. **Sectorial Freeze**: Congelación instantánea de capas o archivos específicos.
5. **Constitutional Snapshots**: Guardado y restauración de perfiles de gobernanza.

## II. AUTONOMÍA Y RIESGO
6. **Autonomy Boundaries**: Presupuesto de riesgo (Risk Budget) acumulativo.
7. **Drift Detector**: Detección de erosión o intentos de saltar restricciones.
8. **Shadow Cooldown**: Enfriamiento obligatorio tras tandas intensas de cambio.
9. **Creator-Only PIN**: Override irrompible para acciones extremas.

## III. RESILIENCIA Y RECUPERACIÓN
10. **Shadow Auditors**: Validación técnica cruzada antes de aplicar cambios.
11. **Conflict Resolution**: Manejo de colisiones entre agentes del enjambre.
12. **Self-Correction Loop**: Re-intento automático de tareas fallidas (Rescue).
13. **Deep Evidence**: Trazabilidad total de por qué se tomó cada decisión.
14. **Global Recovery**: Loop de rescate para nodos en estado FAILED.
15. **Rollback / Checkpoints**: Retorno a estados seguros ante fallas críticas.

**REGLA DE ORO**: El Creador tiene prioridad absoluta. Cualquier bloqueo puede ser levantado mediante Inyección de Autoridad o PIN de Override.
        """

    def close_current_mission(self, reason: str = "Closed by Creator"):
        """
        Explictly closes the active mission to prevent accidental follow-ups.
        Generates a MissionHandoff for the logbook.
        """
        active = self.get_active_mission()
        if active:
            active.status = MissionStatus.COMPLETED
            active.blocked_reasons.append(f"Cierre explícito: {reason}")
            self.save_mission(active)
            
            # Generate and Log Handoff (Ergonomics Phase 21)
            try:
                from .mission_summarizer import mission_summarizer
                handoff = mission_summarizer.summarize(active)
                
                from backend.core.master_logbook.manager import master_logbook_manager
                from backend.core.master_logbook.models import MasterLogbookEntry, EntryType, Priority
                
                entry = MasterLogbookEntry(
                    type=EntryType.MISSION_HANDOFF,
                    content=handoff.executive_summary,
                    priority=Priority.MEDIUM,
                    chip_reference="mission_system",
                    metadata=handoff.model_dump(mode='json')
                )
                master_logbook_manager.add_entry(entry)
                logger.info(f"[MISSION_MANAGER] Handoff generated and logged for {active.mission_id}.")
            except Exception as e:
                logger.error(f"[MISSION_MANAGER] Could not generate handoff: {e}")

            # 4. Trigger Dependency Re-evaluation (Hierarchy Block)
            self.reevaluate_dependents(active.mission_id)

            self.active_mission = None
            logger.info(f"[MISSION_MANAGER] Mission {active.mission_id} closed manually.")

    def get_mission_handoff(self, mission_id: str) -> Optional[MissionHandoff]:
        """Retrieves a handoff for a given mission."""
        from .mission_summarizer import mission_summarizer
        # In a real system, we might cache this in DB, but for now we summarize on demand if closed
        # or fetch from logbook if available. 
        # For simplicity, we fetch the mission state and summarize.
        # This implementation requires get_mission_by_id which is not yet fully implemented, 
        # so we rely on the active one if it matches.
        active = self.get_active_mission()
        if active and active.mission_id == mission_id:
             return mission_summarizer.summarize(active)
        else:
             # Fetch from DB logic (minimal for now)
             with set_chip_context("core"):
                  with db_manager.get_connection() as conn:
                       res = conn.execute("SELECT * FROM system_missions WHERE mission_id = ?", (mission_id,)).fetchone()
                       if res:
                            mission = self._row_to_mission(res)
                            return mission_summarizer.summarize(mission)
        return None

    def _row_to_mission(self, row) -> MissionState:
        # Handle created_at and updated_at being either strings or datetime objects (sqlite3 vs mock)
        created_at = row['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = datetime.now()
        
        updated_at = row['updated_at']
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except:
                updated_at = datetime.now()

        # Handle last_focused_at
        last_f = row['last_focused_at'] if 'last_focused_at' in row.keys() else None
        if isinstance(last_f, str):
            try: last_f = datetime.fromisoformat(last_f)
            except: last_f = datetime.now()
        else:
            last_f = datetime.now()

        return MissionState(
            mission_id=row['mission_id'],
            active_goal=row['active_goal'],
            status=MissionStatus(row['status']),
            plan_id=row['plan_id'],
            completed_steps=json.loads(row['completed_steps'] or '[]'),
            pending_steps=json.loads(row['pending_steps'] or '[]'),
            blocked_reasons=json.loads(row['blocked_reasons'] or '[]'),
            related_targets=json.loads(row['related_targets'] or '[]'),
            parameters=json.loads(row['parameters'] or '{}') if 'parameters' in row.keys() else {},
            context_snap=json.loads(row['context_snap'] or '{}') if 'context_snap' in row.keys() else {},
            visual_context=json.loads(row['visual_context']) if (row.keys() and 'visual_context' in row.keys() and row['visual_context']) else None,
            multimodal_history=json.loads(row['multimodal_history'] or '[]') if (row.keys() and 'multimodal_history' in row.keys() and row['multimodal_history']) else [],
            parent_id=row['parent_id'] if 'parent_id' in row.keys() else None,
            child_ids=json.loads(row['child_ids'] if 'child_ids' in row.keys() and row['child_ids'] else '[]'),
            dependency_ids=json.loads(row['dependency_ids'] if 'dependency_ids' in row.keys() and row['dependency_ids'] else '[]'),
            relation_type=row['relation_type'] if 'relation_type' in row.keys() else None,
            retried_from=row['retried_from'] if 'retried_from' in row.keys() else None,
            branched_from=row['branched_from'] if 'branched_from' in row.keys() else None,
            priority_score=row['priority_score'] if 'priority_score' in row.keys() else 0.0,
            priority_class=row['priority_class'] if 'priority_class' in row.keys() else "NORMAL",
            readiness_state=row['readiness_state'] if 'readiness_state' in row.keys() else "READY",
            compact_digest=MissionCompactDigest.model_validate_json(row['compact_digest']) if (row.keys() and 'compact_digest' in row.keys() and row['compact_digest']) else None,
            last_focused_at=last_f,
            created_at=created_at,
            updated_at=updated_at
        )

mission_manager = MissionManager()
