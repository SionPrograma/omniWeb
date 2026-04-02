import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class MissionStatus(str, Enum):
    OPEN = "OPEN"           # Active mission
    PAUSED = "PAUSED"       # Human interrupted or switched context
    BLOCKED = "BLOCKED"     # Stuck on an issue or verification failure
    COMPLETED = "COMPLETED" # Mission objective reached
    FAILED = "FAILED"       # Critical error or goal unreachable

class MissionState(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    mission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active_goal: str
    status: MissionStatus = MissionStatus.OPEN
    plan_id: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    blocked_reasons: List[str] = Field(default_factory=list)
    related_targets: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict) # mission: is_conservative, audit_only, roadmap_first, etc.
    context_snap: Dict[str, Any] = Field(default_factory=dict)
    telemetry_snap: Dict[str, Any] = Field(default_factory=dict) # Phase 16: Operational Telemetry
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

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
        return cls._instance

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
        return mission

    def save_mission(self, mission: MissionState):
        """
        Persists mission state to SQLite.
        """
        # PHASE 21: Auto-inject core health synthesis
        from backend.core.ai_host.shadow_swarm.approval_gate import approval_gate
        mission.context_snap["governance_health"] = approval_gate.get_governance_health(mission)

        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                query = """
                INSERT OR REPLACE INTO system_missions (
                    mission_id, active_goal, status, plan_id, 
                    completed_steps, pending_steps, blocked_reasons, 
                    related_targets, parameters, context_snap, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                conn.execute(query, (
                    mission.mission_id,
                    mission.active_goal,
                    mission.status.value,
                    mission.plan_id,
                    json.dumps(mission.completed_steps),
                    json.dumps(mission.pending_steps),
                    json.dumps(mission.blocked_reasons),
                    json.dumps(mission.related_targets),
                    json.dumps(mission.parameters),
                    json.dumps(mission.context_snap),
                    datetime.now().isoformat()
                ))
                conn.commit()

    def get_active_mission(self) -> Optional[MissionState]:
        """
        Retrieves the latest OPEN or PAUSED mission.
        """
        if self.active_mission:
            print(f"DEBUG: [MISSION_MANAGER] Active mission status in memory: {self.active_mission.status.value}")
        
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

    def update_step_status(self, step_id: Any, status: str, event_text: str = None, evidence: str = None, deep_evidence: Dict[str, Any] = None):
        """
        Updates a step's status in the execution tree and persistent lists.
        Triggers telemetry updates and deep evidence storage for detailed inspection.
        """
        mission = self.get_active_mission()
        if not mission: return

        # Normalize ID (e.g., from 'plan_job_1' or 1)
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

        # 3. Update Telemetry Snap (Feedback Loop)
        mission.telemetry_snap = {
            "last_event": event_text or f"Subtarea {target_id}: {status}",
            "last_sync": datetime.now().strftime("%H:%M:%S"),
            "status_color": self._get_status_color(status),
            "current_evidence": evidence or (deep_evidence.get('summary') if deep_evidence else None)
        }

        # 4. Global Goal Completion
        if not mission.pending_steps and status == "COMPLETED":
             mission.status = MissionStatus.COMPLETED

        mission.updated_at = datetime.now()
        self.save_mission(mission)
        logger.info(f"[MISSION_MANAGER] Step {target_id} -> {status}")

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

        return MissionState(
            mission_id=row['mission_id'],
            active_goal=row['active_goal'],
            status=MissionStatus(row['status']),
            plan_id=row['plan_id'],
            completed_steps=json.loads(row['completed_steps'] or '[]'),
            pending_steps=json.loads(row['pending_steps'] or '[]'),
            blocked_reasons=json.loads(row['blocked_reasons'] or '[]'),
            related_targets=json.loads(row['related_targets'] or '[]'),
            parameters=json.loads(row.get('parameters', '{}') or '{}'),
            context_snap=json.loads(row['context_snap'] or '{}'),
            created_at=created_at,
            updated_at=updated_at
        )

mission_manager = MissionManager()
