import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from backend.core.ai_host.memory.handoff_manager import handoff_manager, ProposedMission
from backend.core.ai_host.memory.scheduler_manager import scheduler_manager

logger = logging.getLogger(__name__)

class RoadmapGroup(BaseModel):
    group_id: str
    title: str
    type: str = "surface" # surface, manual_epic, domain
    missions: List[Dict[str, Any]] = [] # Active SystemMissions
    handoffs: List[ProposedMission] = [] # Pending/Blocked/Foreclosed
    
    # Metrics
    active_count: int = 0
    ready_count: int = 0
    blocked_count: int = 0
    completed_recent_count: int = 0
    foreclosed_count: int = 0
    
    # Analysis
    health_signal: str = "SANO" # SANO, ESTANCADO, CRITICO, COMPLETADO
    risk_density: float = 0.0
    bottleneck_reason: Optional[str] = None
    
    # Readiness Analysis (Enhanced Phase)
    readiness_state: str = "PENDING" # LAUNCH_READY, PARTIAL_READY, STALLED, DIRTY_BACKLOG, GOVERNANCE_HELD
    readiness_score: float = 0.0 # 0.0 to 1.0
    primary_blocker_id: Optional[str] = None
    blocking_factors: List[str] = []
    enabling_factors: List[str] = []
    next_recommended_action: str = "Inspeccionar dominio"
    
    updated_at: datetime = Field(default_factory=datetime.now)

class CognitiveRoadmap(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.now)
    groups: List[RoadmapGroup] = []
    global_bottlenecks: List[str] = []
    active_dominance: List[str] = [] # Most active surfaces

class RebasePreviewItem(BaseModel):
    handoff_id: str
    title: str
    risk: str
    current_state: str
    rebase_needed: bool = False
    governance_blocks: List[str] = []
    required_actions: List[str] = []
    sequence_index: int = 0

class DomainRebasePlan(BaseModel):
    group_id: str
    domain_name: str
    items: List[RebasePreviewItem] = []
    suggested_sequence: List[str] = []
    risk_summary: str = "Bajo"
    atomic_feasibility: float = 1.0 # 0.0 to 1.0
    critical_blockers: List[str] = []
    next_steps: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.now)

class AtomicPushStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str # REBASE, ACTIVATE, AUDIT
    handoff_id: str
    status: str = "PENDING" # PENDING, RUNNING, COMPLETED, FAILED, BLOCKED
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AtomicPushSession(BaseModel):
    push_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    domain_name: str
    state: str = "READY" # READY, RUNNING, PAUSED, COMPLETED, BLOCKED, ABORTED
    steps: List[AtomicPushStep] = []
    current_step_index: int = 0
    blocking_reason: Optional[str] = None
    authority_required: Optional[str] = None
    is_resolvable: bool = False
    blocked_handoff_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        return cls(
            push_id=row["push_id"],
            group_id=row["roadmap_group_id"],
            domain_name=row.get("domain_name", "Desconocido"),
            state=row["state"],
            current_step_index=row["current_step_index"],
            steps=[AtomicPushStep(**s) for s in json.loads(row["execution_plan"])] if isinstance(row["execution_plan"], str) else (row["execution_plan"] or []),
            blocking_reason=row["blocking_reason"],
            authority_required=row["authority_required"],
            is_resolvable=bool(row.get("is_resolvable", 0)),
            blocked_handoff_id=row.get("blocked_handoff_id"),
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"]
        )

class AtomicRollbackStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_step_type: str # REBASE, ACTIVATE
    handoff_id: str
    status: str = "PENDING" # PENDING, RUNNING, COMPLETED, FAILED, BLOCKED
    revertible: bool = True
    risk: str = "low"
    reason_not_revertible: Optional[str] = None

class AtomicRollbackSession(BaseModel):
    rollback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    push_id: str
    state: str = "PENDING" # PENDING, READY, RUNNING, COMPLETED, BLOCKED, ABORTED
    steps: List[AtomicRollbackStep] = []
    current_step_index: int = 0
    blocking_reason: Optional[str] = None
    authority_required: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        return cls(
            rollback_id=row["rollback_id"],
            push_id=row["push_id"],
            state=row["state"],
            current_step_index=row["current_step_index"],
            steps=[AtomicRollbackStep(**s) for s in json.loads(row["steps"])] if isinstance(row["steps"], str) else (row["steps"] or []),
            blocking_reason=row["blocking_reason"],
            authority_required=row["authority_required"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"]
        )

import uuid
import json
class RoadmapAggregator:
    """
    CAPA 2 & 3: STRATEGIC AGGREGATION ENGINE.
    Consolidates the tactical landscape into cognitive roadmap groups.
    """
    
    def get_macro_roadmap(self, filter_surface: Optional[str] = None, branch_id: str = "main") -> CognitiveRoadmap:
        # 0. State initialization
        groups_dict: Dict[str, RoadmapGroup] = {}
        
        # 1. Fetch all data
        all_handoffs = handoff_manager.get_all(include_archived=True, branch_id=branch_id)
        
        from backend.core.database import db_manager
        active_missions = []
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT mission_id, active_goal, status, related_targets FROM system_missions WHERE status IN ('OPEN', 'ACTIVE', 'PAUSED')")
                for row in cursor.fetchall():
                    active_missions.append(dict(row))
        except Exception as e:
            logger.warning(f"Could not fetch active missions for roadmap: {e}")
        
        # 1b. Process Active Missions
        import json
        for m in active_missions:
            targets = []
            try:
                targets = json.loads(m.get('related_targets', '[]'))
            except: pass
            
            # Simple inference: first target or 'core'
            surface = targets[0] if targets else "core"
            if surface not in groups_dict:
                groups_dict[surface] = RoadmapGroup(
                    group_id=f"surface_{surface}",
                    title=f"Dominio: {surface.upper()}",
                    type="surface"
                )
            groups_dict[surface].active_count += 1
            groups_dict[surface].missions.append(m)

        # 2. Grouping Logic (Primary Basis: Surface - from Handoffs)
        for h in all_handoffs:
            surfaces = h.surface_affected or ["general"]
            for s in surfaces:
                if filter_surface and s != filter_surface: continue
                
                if s not in groups_dict:
                    groups_dict[s] = RoadmapGroup(
                        group_id=f"surface_{s}",
                        title=f"Dominio: {s.upper()}",
                        type="surface"
                    )
                
                g = groups_dict[s]
                
                # Distribution logic
                if h.readiness_state == "ARCHIVED":
                    if h.foreclosure.status == "FORECLOSED":
                        g.foreclosed_count += 1
                    else:
                        g.completed_recent_count += 1
                elif h.readiness_state == "BLOCKED":
                    g.blocked_count += 1
                elif h.readiness_state == "READY":
                    g.ready_count += 1
                else:
                    g.active_count += 1
                
                g.handoffs.append(h)

        # 3. Health & Readiness Analysis per Group
        global_issues = []
        for s, g in groups_dict.items():
            # --- Metrics Calc ---
            total_tactical = g.active_count + g.ready_count + g.blocked_count
            foreclose_candidates = len([h for h in g.handoffs if h.foreclosure.status in ["CANDIDATE_FORECLOSE", "CANDIDATE_ARCHIVE"]])
            
            # --- Health Signal (Existing) ---
            if g.blocked_count > total_tactical * 0.5 and total_tactical > 0:
                g.health_signal = "ESTANCADO"
                g.bottleneck_reason = f"Más del 50% de las misiones en '{s}' están bajo bloqueo de gobernanza o rebase."
                global_issues.append(f"Cuello de botella en superficie: {s}")
            elif g.blocked_count > 0 and g.active_count == 0:
                g.health_signal = "CRITICO"
                g.bottleneck_reason = "Todas las misiones tácticas están bloqueadas sin ejecución activa."
            
            # --- Readiness Analysis (New) ---
            g.blocking_factors = []
            g.enabling_factors = []
            
            # Determine Readiness State
            if total_tactical == 0:
                if g.completed_recent_count > 0:
                    g.readiness_state = "COMPLETADO"
                    g.readiness_score = 1.0
                else:
                    g.readiness_state = "PENDING"
            else:
                # Calculate Factors
                if g.blocked_count > 0:
                    g.blocking_factors.append(f"{g.blocked_count} misiones bloqueadas")
                
                # Default state
                g.readiness_state = "STALLED"
                g.next_recommended_action = "Activar misiones pendientes"

                # Priority 1: Dirty Backlog (Noisy)
                if foreclose_candidates > 0:
                    g.blocking_factors.append(f"{foreclose_candidates} propuestas obsoletas/ruido")
                    g.readiness_state = "DIRTY_BACKLOG"
                    g.next_recommended_action = f"Ejecutar AUDIT CIERRES en {s}"

                # Priority 2: Governance (Held)
                gov_locks = len([h for h in g.handoffs if h.readiness_state == "BLOCKED" and h.risk_level == "high"])
                if gov_locks > 0:
                    g.blocking_factors.append(f"{gov_locks} misiones retenidas por GOBERNANZA")
                    g.readiness_state = "GOVERNANCE_HELD"
                    g.next_recommended_action = "Revisar GATES de seguridad"

                # Priority 3: Ready or Partial Ready (only if no higher priority locks)
                if g.readiness_state not in ["DIRTY_BACKLOG", "GOVERNANCE_HELD"]:
                    if g.blocked_count == 0 and g.active_count > 0 and foreclose_candidates == 0:
                        g.readiness_state = "LAUNCH_READY"
                        g.readiness_score = 0.9
                        g.enabling_factors.append("Cero bloqueos activos")
                        g.enabling_factors.append("Ejecución nominal")
                        g.next_recommended_action = "Empujar a Producción"
                    elif g.active_count > 0:
                        g.readiness_state = "PARTIAL_READY"
                        g.readiness_score = 0.6
                        g.next_recommended_action = "Resolver bloqueos menores"

                # Find Primary Blocker
                blocked_missions = [h for h in g.handoffs if h.readiness_state == "BLOCKED"]
                if blocked_missions:
                    g.primary_blocker_id = blocked_missions[0].handoff_id

            # Risk density (simulation based on logic)
            g.risk_density = (g.blocked_count * 0.4) + (g.active_count * 0.1) + (foreclose_candidates * 0.05)

        roadmap = CognitiveRoadmap(
            groups=list(groups_dict.values()),
            global_bottlenecks=global_issues,
            active_dominance=sorted(groups_dict.keys(), key=lambda x: groups_dict[x].active_count, reverse=True)[:3]
        )
        
        return roadmap

    def get_domain_preview(self, group_id: str) -> DomainRebasePlan:
        """
        CAPA 2: DOMAIN PREVIEW ENGINE.
        Generates an atomic rebase plan for the selected domain/surface.
        """
        # 1. Fetch group data
        macro = self.get_macro_roadmap()
        group = next((g for g in macro.groups if g.group_id == group_id), None)
        if not group:
            raise ValueError(f"Domain group {group_id} not found.")

        domain_name = group.title.replace("Dominio: ", "").lower()
        items = []
        
        # 2. Analyze each tactical element (Handoffs)
        from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
        
        # Analyze the sequence for this group specifically
        h_ids = [h.handoff_id for h in group.handoffs]
        
        from backend.core.ai_host.memory.scheduler_manager import MissionSchedule
        temp_schedule = MissionSchedule(ordered_handoff_ids=h_ids)
        temp_schedule.rebase_required_flags = [] # Initialize
        
        audit_results = {}
        if h_ids:
             # Simulation of a schedule audit
             audit_results = scheduler_manager.audit_launch_readiness(temp_schedule, group.handoffs) 
        
        suggested_order = h_ids # Default
        try:
            # Try to get an optimized sequence if there are multiple items
            if len(h_ids) > 1:
                seq_proposal = scheduler_manager.compute_optimized_sequence(temp_schedule, group.handoffs)
                suggested_order = seq_proposal.suggested_order
        except Exception as e:
            logger.warning(f"Could not compute optimized sequence for preview: {e}")

        # 3. Map to Preview Items
        critical_blockers = []
        for h_id in suggested_order:
            h = next((x for x in group.handoffs if x.handoff_id == h_id), None)
            if not h: continue
            
            # Check rebase status
            rebase_report = handoff_manager.check_rebase(h_id)
            audit = audit_results.get(h_id)
            
            blocks = []
            if audit: blocks.extend(audit.blocks)
            if rebase_report["status"] in ["CONFLICTED", "NEEDS_REFRESH"]:
                blocks.append("REBASE_REQUIRED")
                
            item = RebasePreviewItem(
                handoff_id=h_id,
                title=h.briefing_title,
                risk=h.risk_level,
                current_state=h.readiness_state,
                rebase_needed=rebase_report["status"] != "STILL_VALID",
                governance_blocks=blocks,
                required_actions=audit.required_actions if audit else [],
                sequence_index=suggested_order.index(h_id) + 1
            )
            items.append(item)
            if any(b in ["NEEDS_PIN", "AUTHORITY_EXPIRED", "CRITICAL_DRIFT"] for b in blocks):
                critical_blockers.append(f"Misión {h_id[:6]} requiere intervención manual.")

        # 4. Feasibility
        feasibility = 1.0
        if critical_blockers: feasibility -= 0.5
        if not items: feasibility = 0.0
        
        next_steps = []
        if group.readiness_state == "DIRTY_BACKLOG":
            next_steps.append("Ejecutar limpieza de backlog obsoleta.")
        if critical_blockers:
            next_steps.append("Resolver bloqueos de autoridad en misiones críticas.")
        if feasibility > 0.8:
            next_steps.append("Confirmar empuje atómico.")

        return DomainRebasePlan(
            group_id=group_id,
            domain_name=domain_name,
            items=items,
            suggested_sequence=suggested_order,
            risk_summary=f"Densidad de Riesgo: {(group.risk_density * 100):.1f}%",
            atomic_feasibility=max(0.1, feasibility),
            critical_blockers=critical_blockers,
            next_steps=next_steps
        )

    # --- ATOMIC PUSH EXECUTION ENGINE ---
    
    def start_push_session(self, group_id: str) -> AtomicPushSession:
        """CAPA 2: Inicia un hilo de ejecución atómica para un dominio."""
        plan = self.get_domain_preview(group_id)
        if not plan:
            raise ValueError(f"No roadmap plan found for group {group_id}")
            
        session = AtomicPushSession(
            group_id=group_id,
            domain_name=plan.domain_name,
            steps=[
                AtomicPushStep(type="REBASE" if i.rebase_needed else "ACTIVATE", handoff_id=i.handoff_id)
                for i in plan.items
            ],
            current_step_index=0
        )
        self._save_session(session)
        
        # FORENSICS: Start Log
        self._log_event(
            session.push_id, "PUSH_STARTED", 
            payload={"domain": plan.domain_name, "total_steps": len(session.steps)}
        )
        
        logger.info(f"ATOMIC PUSH: Session {session.push_id} started for domain {plan.domain_name}")
        return session

    def execute_next_step(self, push_id: str) -> AtomicPushSession:
        """CAPA 2: Ejecución secuencial gobernada."""
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            session = self.get_session(push_id)
            if not session: raise ValueError("Push session not found")
            
            if session.state not in ["RUNNING", "READY"]:
                return session

            if session.current_step_index >= len(session.steps):
                session.state = "COMPLETED"
                self._save_session(session)
                return session

            step = session.steps[session.current_step_index]
            step.status = "RUNNING"
            step.started_at = datetime.now()
            
            # 1. GOVERNANCE CHECK (PHASE 91 REUSE)
            from backend.core.ai_host.memory.scheduler_manager import MissionSchedule
            h = handoff_manager.get_proposal(step.handoff_id)
            if not h:
                step.status = "FAILED"
                step.error = "Handoff vanished"
                session.state = "FAILED_SAFELY"
                self._save_session(session)
                return session

            # Verify gates
            audit = scheduler_manager.audit_launch_readiness(MissionSchedule(rebase_required_flags=[]), [h])
            status = audit.get(h.handoff_id)
            
            if not status or not status.is_ready:
                session.state = "BLOCKED"
                session.blocking_reason = status.rationale if status else "Falla en Gate Analyzer"
                session.authority_required = ", ".join(status.blocks) if status else "Desconocido"
                
                # Check for resolvable authority blocks
                resolvable_blocks = ["NEEDS_PIN", "AUTHORITY_EXPIRED", "WAITING_AUTHORITY"]
                if any(b in resolvable_blocks for b in (status.blocks if status else [])):
                    session.is_resolvable = True
                    session.blocked_handoff_id = h.handoff_id
                
                step.status = "BLOCKED"
                self._save_session(session)
                
                # FORENSICS: Blocked step
                self._log_event(
                    session.push_id, "STEP_BLOCKED", session.current_step_index, h.handoff_id,
                    payload={"reason": session.blocking_reason, "authority": session.authority_required}
                )
                
                return session

            # 2. EXECUTION
            try:
                if step.type == "REBASE":
                    self._log_event(session.push_id, "STEP_REBASE_START", session.current_step_index, h.handoff_id)
                    handoff_manager.update_proposal(h.handoff_id, {
                        "updated_at": datetime.now(),
                        "metadata": {"rebased_at": datetime.now().isoformat()}
                    })
                    logger.info(f"ATOMIC PUSH: Rebase executed for {h.handoff_id}")
                
                elif step.type == "ACTIVATE":
                    self._log_event(session.push_id, "STEP_ACTIVATE_START", session.current_step_index, h.handoff_id)
                    handoff_manager.update_proposal(h.handoff_id, {"readiness_state": "PENDING"})
                    logger.info(f"ATOMIC PUSH: Mission activated {h.handoff_id}")

                step.status = "COMPLETED"
                step.completed_at = datetime.now()
                self._log_event(session.push_id, "STEP_COMPLETED", session.current_step_index, h.handoff_id)
                
                session.current_step_index += 1
                
                if session.current_step_index >= len(session.steps):
                    session.state = "COMPLETED"
                    self._log_event(session.push_id, "PUSH_COMPLETED")

            except Exception as e:
                step.status = "FAILED"
                step.error = str(e)
                session.state = "FAILED_SAFELY"
                logger.error(f"ATOMIC PUSH: Step failed: {e}")

            session.updated_at = datetime.now()
            self._save_session(session)
            return session

    def abort_push(self, push_id: str):
        session = self.get_session(push_id)
        if session:
            session.state = "ABORTED"
            self._save_session(session)
            self._log_event(push_id, "PUSH_ABORTED")
            logger.warning(f"ATOMIC PUSH: Session {push_id} aborted by creator")

    def inject_authority(self, push_id: str, pin: str) -> AtomicPushSession:
        """CAPA 3: Inyección de autoridad y reanudación segura."""
        from backend.core.config import settings
        if pin != settings.CREATOR_PIN:
            logger.warning(f"ATOMIC PUSH: Authority injection failed. Invalid PIN.")
            self._log_event(push_id, "AUTHORITY_REJECTED", payload={"reason": "Invalid PIN"})
            raise ValueError("Invalid PIN")
            
        session = self.get_session(push_id)
        if not session or not session.is_resolvable:
             raise ValueError("No resolvable authority block found.")
             
        # Resolve the handoff gate
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            h = handoff_manager.get_proposal(session.blocked_handoff_id)
            if h:
                gate = h.gate_data or {}
                gate["verified"] = True
                gate["authority_session_active"] = True
                handoff_manager.update_proposal(h.handoff_id, {"gate_data": gate})
                logger.info(f"ATOMIC PUSH: Authority injected for handoff {h.handoff_id}")
                
            # FORENSICS: Authority injected
            self._log_event(
                push_id, "AUTHORITY_INJECTED", session.current_step_index, 
                session.blocked_handoff_id, actor="creator"
            )
            
            # Reset session block and resume
            session.state = "RUNNING"
            session.is_resolvable = False
            session.blocking_reason = None
            session.authority_required = None
            self._save_session(session)
            
            # Re-execute the step now that the gate is clear
            return self.execute_next_step(push_id)

    def get_forensics(self, push_id: str) -> List[Dict[str, Any]]:
        """CAPA 4: Reconstrucción forense del historial del push."""
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM atomic_push_forensics 
                    WHERE push_id = ? 
                    ORDER BY timestamp ASC
                """, (push_id,)).fetchall()
                return [dict(r) for r in rows]

    def _log_event(self, push_id: str, event_type: str, step_index: Optional[int] = None, 
                  handoff_id: Optional[str] = None, payload: Optional[Dict] = None, 
                  actor: str = "creator"):
        """CAPA 2: Registro de telemetría táctica con integridad."""
        import hashlib
        payload_str = json.dumps(payload or {})
        
        # Simple Integrity Base
        sig_base = f"{push_id}:{event_type}:{step_index}:{handoff_id}:{payload_str}"
        integrity_hash = hashlib.sha256(sig_base.encode()).hexdigest()
        
        try:
            from backend.core.database import db_manager
            from backend.core.permissions import set_chip_context
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO atomic_push_forensics (
                            push_id, event_type, step_index, handoff_id, actor, payload, integrity_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        push_id, event_type, step_index, handoff_id, actor, payload_str, integrity_hash
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"FORENSICS: Failed to log event {event_type} for push {push_id}: {e}")

    def get_session(self, push_id: str) -> Optional[AtomicPushSession]:
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT * FROM atomic_push_sessions WHERE push_id = ?", (push_id,)).fetchone()
                if row:
                    return AtomicPushSession.from_row(dict(row))
        return None

    def _save_session(self, session: AtomicPushSession):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO atomic_push_sessions (
                        push_id, roadmap_group_id, state, current_step_index, 
                        execution_plan, step_statuses, blocking_reason, authority_required,
                        is_resolvable, blocked_handoff_id,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    session.push_id, session.group_id, session.state, session.current_step_index,
                    json.dumps([s.model_dump(mode='json') for s in session.steps]),
                    json.dumps({i: s.status for i, s in enumerate(session.steps)}),
                    session.blocking_reason, session.authority_required,
                    int(session.is_resolvable), session.blocked_handoff_id
                ))
                conn.commit()

    # --- GOVERNED ROLLBACK ENGINE ---

    def preview_rollback(self, push_id: str) -> AtomicRollbackSession:
        """CAPA 2: Genera un plan de reversión basado en evidencia forense."""
        forensics = self.get_forensics(push_id)
        if not forensics:
            raise ValueError(f"No forensics found for push {push_id}. Rollback impossible.")
            
        # Reconstruct successful steps in reverse order
        steps_to_revert = []
        completed_events = [e for e in forensics if e["event_type"] == "STEP_COMPLETED"]
        
        # Sort by timestamp desc to revert in inverse order
        completed_events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            for event in completed_events:
                h_id = event["handoff_id"]
                h = handoff_manager.get_proposal(h_id)
                if not h: continue
                
                # Logic to determine revertibility
                revertible = True
                risk = "low"
                reason = None
                
                # Determine original step type from forensics or session
                # For now, we infer from handoff state
                original_type = "ACTIVATE" # Default
                # In real push, it could be REBASE
                # Check forensics payload
                start_event = next((e for e in forensics if e["event_type"] in ["STEP_ACTIVATE_START", "STEP_REBASE_START"] and e["step_index"] == event["step_index"]), {})
                if "REBASE" in start_event.get("event_type", ""):
                    original_type = "REBASE"
                
                if original_type == "ACTIVATE":
                    if h.readiness_state not in ["PENDING", "ACTIVE"]:
                         revertible = False
                         risk = "high"
                         reason = f"Misión ya avanzó a estado {h.readiness_state}"
                elif original_type == "REBASE":
                    meta = h.metadata or {}
                    if "rebased_at" not in meta:
                        revertible = False
                        risk = "high"
                        reason = "Los metadatos del rebase ya no existen."

                steps_to_revert.append(AtomicRollbackStep(
                    original_step_type=original_type,
                    handoff_id=h_id,
                    revertible=revertible,
                    risk=risk,
                    reason_not_revertible=reason
                ))
                
        session = AtomicRollbackSession(push_id=push_id, steps=steps_to_revert)
        self._save_rollback_session(session)
        
        # FORENSICS: Rollback preview
        self._log_event(push_id, "ROLLBACK_PREVIEW_GENERATED", payload={"rollback_id": session.rollback_id})
        
        return session

    def start_rollback(self, rollback_id: str) -> AtomicRollbackSession:
        """CAPA 4: Inicia la ejecución del rollback."""
        session = self.get_rollback_session(rollback_id)
        if not session: raise ValueError("Rollback session not found.")
        
        if session.state != "PENDING":
             return session
             
        session.state = "RUNNING"
        self._save_rollback_session(session)
        self._log_event(session.push_id, "ROLLBACK_STARTED", payload={"rollback_id": rollback_id})
        
        return session

    def execute_next_rollback_step(self, rollback_id: str) -> AtomicRollbackSession:
        """CAPA 4: Ejecución gobernada paso a paso de la reversión."""
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            session = self.get_rollback_session(rollback_id)
            if not session or session.state != "RUNNING": return session
            
            if session.current_step_index >= len(session.steps):
                session.state = "COMPLETED"
                self._save_rollback_session(session)
                self._log_event(session.push_id, "ROLLBACK_COMPLETED")
                return session
                
            step = session.steps[session.current_step_index]
            if not step.revertible:
                # Safe skip or partial block
                session.current_step_index += 1
                self._save_rollback_session(session)
                self._log_event(session.push_id, "ROLLBACK_STEP_SKIPPED", session.current_step_index, step.handoff_id)
                return self.execute_next_rollback_step(rollback_id)
                
            step.status = "RUNNING"
            try:
                # Inverse Logic
                if step.original_step_type == "ACTIVATE":
                    handoff_manager.update_proposal(step.handoff_id, {"readiness_state": "READY"})
                elif step.original_step_type == "REBASE":
                    h = handoff_manager.get_proposal(step.handoff_id)
                    meta = h.metadata or {}
                    if "rebased_at" in meta:
                        del meta["rebased_at"]
                    handoff_manager.update_proposal(step.handoff_id, {"metadata": meta})
                
                step.status = "COMPLETED"
                self._log_event(session.push_id, "ROLLBACK_STEP_COMPLETED", session.current_step_index, step.handoff_id)
            except Exception as e:
                logger.error(f"ROLLBACK: Step failed: {e}")
                step.status = "FAILED"
                session.state = "FAILED_SAFELY"
                self._log_event(session.push_id, "ROLLBACK_STEP_FAILED", payload={"error": str(e)})
            
            session.current_step_index += 1
            if session.current_step_index >= len(session.steps):
                session.state = "COMPLETED"
                self._log_event(session.push_id, "ROLLBACK_COMPLETED")
                
            self._save_rollback_session(session)
            return session

    def get_rollback_session(self, rollback_id: str) -> Optional[AtomicRollbackSession]:
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT * FROM atomic_rollback_sessions WHERE rollback_id = ?", (rollback_id,)).fetchone()
                if row:
                    return AtomicRollbackSession.from_row(dict(row))
        return None

    def _save_rollback_session(self, session: AtomicRollbackSession):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO atomic_rollback_sessions (
                        rollback_id, push_id, state, steps, current_step_index,
                        blocking_reason, authority_required, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    session.rollback_id, session.push_id, session.state,
                    json.dumps([s.model_dump(mode='json') for s in session.steps]),
                    session.current_step_index, session.blocking_reason, session.authority_required
                ))
                conn.commit()


roadmap_aggregator = RoadmapAggregator()
