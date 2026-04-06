import uuid
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.handoff_manager import handoff_manager, ProposedMission

logger = logging.getLogger(__name__)

class ResolutionSuggestion(BaseModel):
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handoff_ids: List[str] = []
    type: str # REORDER, REBASE, ARCHIVE, PAUSE, RISK_SPLIT
    action_cmd: str
    label: str
    rationale: str
    impact: str = "nominal" # nominal, high, critical
    is_actionable: bool = True

class SequenceProposal(BaseModel):
    suggested_order: List[str] = []
    confidence: float = 1.0
    rationale: str = ""
    cycles_detected: List[List[str]] = []
    risk_gaps_added: int = 0

class MissionGateStatus(BaseModel):
    handoff_id: str
    is_ready: bool = False
    blocks: List[str] = [] # PIN, REBASE, AUTHORITY, LOCK, CONSTITUTIONAL
    required_actions: List[str] = []
    rationale: str = ""
    gate_color: str = "#ff4444" # green, orange, red

class ReorderAnalysis(BaseModel):
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_id: str
    previous_order: List[str]
    proposed_order: List[str]
    readiness_delta: float = 0.0 # Change in readiness score
    newly_ready_ids: List[str] = []
    newly_blocked_ids: List[str] = []
    broken_dependencies: List[Dict[str, str]] = [] # {handoff_id: reason}
    improved_readiness: bool = False
    risk_impact: str = "neutral" # improved, neutral, worsened
    rebase_pressure_delta: int = 0 # Change in number of required rebases
    timestamp: datetime = Field(default_factory=datetime.now)

class MissionSchedule(BaseModel):
    schedule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Nuevo Plan Táctico"
    ordered_handoff_ids: List[str] = Field(default_factory=list)
    dependency_hints: Dict[str, Any] = Field(default_factory=dict)
    risk_chain: Dict[str, Any] = Field(default_factory=dict)
    conflict_chain: Dict[str, Any] = Field(default_factory=dict)
    rebase_required_flags: List[str] = Field(default_factory=list)
    suggestions: List[ResolutionSuggestion] = Field(default_factory=list)
    sequence_proposal: Optional[SequenceProposal] = None
    launch_audit: Dict[str, MissionGateStatus] = Field(default_factory=dict)
    recommended_sequence: List[str] = Field(default_factory=list)
    readiness_state: str = "DRAFT" # DRAFT, READY, EXECUTING, ARCHIVED
    branch_id: str = "main"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        return cls(
            schedule_id=row["schedule_id"],
            title=row["title"],
            ordered_handoff_ids=json.loads(row["ordered_handoff_ids"]) if isinstance(row["ordered_handoff_ids"], str) else (row["ordered_handoff_ids"] or []),
            dependency_hints=json.loads(row["dependency_hints"]) if row["dependency_hints"] and isinstance(row["dependency_hints"], str) else (row["dependency_hints"] or {}),
            risk_chain=json.loads(row["risk_chain"]) if row["risk_chain"] and isinstance(row["risk_chain"], str) else (row["risk_chain"] or {}),
            conflict_chain=json.loads(row["conflict_chain"]) if row["conflict_chain"] and isinstance(row["conflict_chain"], str) else (row["conflict_chain"] or {}),
            rebase_required_flags=json.loads(row["rebase_required_flags"]) if row["rebase_required_flags"] and isinstance(row["rebase_required_flags"], str) else (row["rebase_required_flags"] or []),
            suggestions=[ResolutionSuggestion(**s) for s in json.loads(row["suggestions"])] if row["suggestions"] and isinstance(row["suggestions"], str) else [],
            sequence_proposal=SequenceProposal(**json.loads(row["sequence_proposal"])) if row["sequence_proposal"] and isinstance(row["sequence_proposal"], str) else None,
            launch_audit={k: MissionGateStatus(**v) for k, v in json.loads(row["launch_audit"]).items()} if row["launch_audit"] and isinstance(row["launch_audit"], str) else {},
            recommended_sequence=json.loads(row["recommended_sequence"]) if row["recommended_sequence"] and isinstance(row["recommended_sequence"], str) else (row["recommended_sequence"] or []),
            readiness_state=row["readiness_state"],
            branch_id=row["branch_id"] if "branch_id" in row.keys() else "main",
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"]
        )

class SchedulerManager:
    """
    CAPA 1, 2 & 3 (PHASE MULTI-MISSION): SCHEDULER ENGINE.
    Enables planning, ordering and analyzing sequences of mission proposals.
    """
    
    def create_schedule(self, title: str, handoff_ids: Optional[List[str]] = None) -> MissionSchedule:
        schedule = MissionSchedule(title=title, ordered_handoff_ids=handoff_ids or [])
        self._save(schedule)
        return schedule

    def get_all(self, include_archived: bool = False) -> List[MissionSchedule]:
        """Alias for list_schedules."""
        return self.list_schedules(include_archived)

    def add_mission_to_sequence(self, schedule_id: str, handoff_id: str):
        schedule = self.get_schedule(schedule_id)
        if not schedule: return
        if handoff_id not in schedule.ordered_handoff_ids:
            schedule.ordered_handoff_ids.append(handoff_id)
            self._save(schedule)
            self.analyze_sequence(schedule_id)

    def update_sequence(self, schedule_id: str, handoff_ids: List[str]):
        """Alias for update_order with re-analysis."""
        self.update_order(schedule_id, handoff_ids)

    def _save(self, schedule: MissionSchedule, conn: Optional[sqlite3.Connection] = None):
        with set_chip_context("core"):
            if conn:
                self._execute_save(conn, schedule)
            else:
                with db_manager.get_connection() as new_conn:
                    self._execute_save(new_conn, schedule)
                    new_conn.commit()

    def _execute_save(self, conn, schedule):
        conn.execute("""
            INSERT OR REPLACE INTO mission_schedules (
                schedule_id, title, ordered_handoff_ids, dependency_hints, 
                risk_chain, conflict_chain, rebase_required_flags, suggestions,
                sequence_proposal, launch_audit, recommended_sequence, readiness_state, branch_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            schedule.schedule_id, schedule.title, json.dumps(schedule.ordered_handoff_ids),
            json.dumps(schedule.dependency_hints), json.dumps(schedule.risk_chain),
            json.dumps(schedule.conflict_chain), json.dumps(schedule.rebase_required_flags),
            json.dumps([s.model_dump() for s in schedule.suggestions]),
            json.dumps(schedule.sequence_proposal.model_dump()) if schedule.sequence_proposal else None,
            json.dumps({k: v.model_dump() for k, v in schedule.launch_audit.items()}),
            json.dumps(schedule.recommended_sequence), schedule.readiness_state, schedule.branch_id
        ))

    def get_schedule(self, schedule_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[MissionSchedule]:
        with set_chip_context("core"):
            if conn:
                return self._execute_get(conn, schedule_id)
            else:
                with db_manager.get_connection() as new_conn:
                    return self._execute_get(new_conn, schedule_id)

    def _execute_get(self, conn, schedule_id):
        row = conn.execute("SELECT * FROM mission_schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
        if row:
            return MissionSchedule.from_row(dict(row))
        return None

    def list_schedules(self, include_archived: bool = False, conn: Optional[sqlite3.Connection] = None) -> List[MissionSchedule]:
        with set_chip_context("core"):
            if conn:
                return self._execute_list(conn, include_archived)
            else:
                with db_manager.get_connection() as new_conn:
                    return self._execute_list(new_conn, include_archived)

    def _execute_list(self, conn, include_archived=False):
        query = "SELECT * FROM mission_schedules WHERE readiness_state != 'ARCHIVED'"
        if include_archived:
            query = "SELECT * FROM mission_schedules"
        rows = conn.execute(f"{query} ORDER BY created_at DESC").fetchall()
        return [MissionSchedule.from_row(dict(row)) for row in rows]

    def analyze_sequence(self, schedule_id: str) -> MissionSchedule:
        """
        CAPA 2: SEQUENCE ANALYSIS ENGINE.
        Analyzes a sequence of missions to find conflicts and dependencies.
        """
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found.")

        handoffs = []
        for h_id in schedule.ordered_handoff_ids:
            h = handoff_manager.get_proposal(h_id)
            if h:
                handoffs.append(h)

        # 1. Reset analysis
        schedule.dependency_hints = {}
        schedule.risk_chain = {}
        schedule.conflict_chain = {}
        schedule.rebase_required_flags = []
        
        # Track surfaces globally for deep analysis (Phase 90)
        global_surface_map = {} # surface -> [handoff_id, ...]
        for h in handoffs:
            for s in (h.surface_affected or []):
                if s not in global_surface_map:
                    global_surface_map[s] = []
                global_surface_map[s].append(h.handoff_id)

        # Track surfaces being modified as we go through the sequence (for sequential conflicts)
        surface_owner = {} 
        
        for i, h in enumerate(handoffs):
            h_id = h.handoff_id
            surfaces = h.surface_affected or []
            
            # --- CONFLICT DETECTION (SEQUENTIAL) ---
            for s in surfaces:
                if s in surface_owner:
                    for prev_id in surface_owner[s]:
                        schedule.conflict_chain[h_id] = schedule.conflict_chain.get(h_id, [])
                        schedule.conflict_chain[h_id].append({
                            "type": "SURFACE_COLLISION",
                            "surface": s,
                            "with_handoff": prev_id,
                            "reason": f"Misión anterior '{prev_id[:6]}' también modifica {s}. Se requiere rebase."
                        })
                        if h_id not in schedule.rebase_required_flags:
                            schedule.rebase_required_flags.append(h_id)

                if s not in surface_owner: surface_owner[s] = []
                surface_owner[s].append(h_id)

        # --- GLOBAL DEPENDENCY ANALYSIS ---
        # Detect all potential implicit dependencies regardless of current order
        for h in handoffs:
            for s, owners in global_surface_map.items():
                if s.lower() in h.objective.lower():
                    for owner in owners:
                        if owner != h.handoff_id:
                            # Potential dependency: owner -> h.handoff_id
                            schedule.dependency_hints[h.handoff_id] = schedule.dependency_hints.get(h.handoff_id, [])
                            if not any(d["depends_on"] == owner for d in schedule.dependency_hints[h.handoff_id]):
                                # Check if current order violates it
                                idx_own = schedule.ordered_handoff_ids.index(owner)
                                idx_h = schedule.ordered_handoff_ids.index(h.handoff_id)
                                status = "SATISFIED" if idx_own < idx_h else "VIOLATED"
                                
                                schedule.dependency_hints[h.handoff_id].append({
                                    "type": "IMPLICIT_DEPENDENCY",
                                    "surface": s,
                                    "depends_on": owner,
                                    "status": status,
                                    "reason": f"Esta misión parece depender de {s} ({owner[:6]}). " + 
                                              ("Orden correcto." if status == "SATISFIED" else "¡VIOLACIÓN DE ORDEN!")
                                })

            # Check for risk accumulation
            if h.risk_level == "high":
                schedule.risk_chain[h_id] = "HIGH_RISK_NODE"
                if i > 0 and handoffs[i-1].risk_level == "high":
                    schedule.risk_chain[h_id] = "CRITICAL_CHAIN_RISK"
                    # Chain of high risks

        # RECOMMENDED SEQUENCE (Simplified: move more ready/lower risk up)
        # For now, we'll keep the current order but flag if reordering is suggested
        # (This could be expanded to a topological sort based on dependency_hints)
        schedule.recommended_sequence = schedule.ordered_handoff_ids # Placeholder
        
        # --- PHASE 2: RESOLUTION ENGINE (BLOCK 89) ---
        schedule.suggestions = []
        
        # 1. Collision -> Reorder / Rebase Suggestion
        for h_id, conflicts in schedule.conflict_chain.items():
            for c in conflicts:
                if c["type"] == "SURFACE_COLLISION":
                    # Suggest rebase after executing the first one
                    schedule.suggestions.append(ResolutionSuggestion(
                        handoff_ids=[c["with_handoff"], h_id],
                        type="REBASE",
                        action_cmd=f"REBASE MISSION HANDOFF {h_id}",
                        label=f"Tactical Rebase: {h_id[:6]}",
                        rationale=f"La misión anterior modifica {c['surface']}. Rebasear {h_id[:6]} asegura compatibilidad tras el primer cambio.",
                        impact="high"
                    ))
        
        # 2. Dependency -> Move Up Suggestion
        for h_id, hints in schedule.dependency_hints.items():
            for d in hints:
                if d["type"] == "IMPLICIT_DEPENDENCY":
                    schedule.suggestions.append(ResolutionSuggestion(
                        handoff_ids=[d["depends_on"], h_id],
                        type="REORDER",
                        action_cmd="SHOW MISSION SCHEDULE", # Just UI focus for now
                        label=f"Priorizar Dependencia: {d['depends_on'][:6]}",
                        rationale=f"{h_id[:6]} parece depender de {d['surface']}. Asegúrate de que {d['depends_on'][:6]} se ejecute primero.",
                        impact="nominal"
                    ))

        # 3. Risk Chain -> Split Suggestion
        for h_id, risk_type in schedule.risk_chain.items():
            if risk_type == "CRITICAL_CHAIN_RISK":
                 schedule.suggestions.append(ResolutionSuggestion(
                    handoff_ids=[h_id],
                    type="RISK_SPLIT",
                    action_cmd="SHOW MISSION SCHEDULE",
                    label="Desacoplar Cadena de Riesgo",
                    rationale="Demasiadas misiones críticas seguidas. Se sugiere insertar una pausa o una misión de bajo riesgo.",
                    impact="critical"
                ))

        # 4. Obsolete Check (Integration with HandoffManager)
        for h_id in schedule.ordered_handoff_ids:
            try:
                report = handoff_manager.check_rebase(h_id)
                if report.get("status") == "OBSOLETE":
                    schedule.suggestions.append(ResolutionSuggestion(
                        handoff_ids=[h_id],
                        type="ARCHIVE",
                        action_cmd=f"ARCHIVE MISSION HANDOFF {h_id}",
                        label=f"Archivar Obsoleta: {h_id[:6]}",
                        rationale="OmniWeb detectó que esta misión ya fue resuelta o es redundante.",
                        impact="nominal"
                    ))
            except: pass

        # --- PHASE 3: TOPOLOGICAL AUTO-SEQUENCER (BLOCK 90) ---
        schedule.sequence_proposal = self.compute_optimized_sequence(schedule, handoffs)
        schedule.recommended_sequence = schedule.sequence_proposal.suggested_order
        
        # --- PHASE 4: GOVERNANCE-GATE ANALYZER (BLOCK 91) ---
        schedule.launch_audit = self.audit_launch_readiness(schedule, handoffs)
        
        # Readiness Update (Governed by Audit)
        all_ready = all(audit.is_ready for audit in schedule.launch_audit.values())
        if all_ready and schedule.ordered_handoff_ids:
             schedule.readiness_state = "READY"
        else:
             schedule.readiness_state = "DRAFT"

        self._save(schedule)
        return schedule

    def audit_launch_readiness(self, schedule: MissionSchedule, handoffs: List[ProposedMission]) -> Dict[str, MissionGateStatus]:
        """
        CAPA 2: GATE ANALYZER ENGINE.
        Verifies if each mission satisfies its governance gates.
        """
        audit_results = {}
        
        for h in handoffs:
            h_id = h.handoff_id
            status = MissionGateStatus(handoff_id=h_id, is_ready=True)
            blocks = []
            actions = []
            
            # 1. Rebase Gate
            if h_id in schedule.rebase_required_flags:
                blocks.append("NEEDS_REBASE")
                actions.append(f"REBASE MISSION HANDOFF {h_id}")
                status.is_ready = False
            
            # 2. Dependency Gate
            hints = schedule.dependency_hints.get(h_id, [])
            if any(h["status"] == "VIOLATED" for h in hints):
                 blocks.append("DEPENDENCY_VIOLATION")
                 actions.append("MOVE MISSION DOWN IN SEQUENCE")
                 status.is_ready = False
            
            # 3. PIN / Confirmation Gate
            gate = h.gate_data or {}
            if gate.get("type") == "PIN" and not gate.get("verified", False):
                blocks.append("NEEDS_PIN")
                actions.append(f"VERIFY PIN FOR {h_id}")
                status.is_ready = False
            
            # Additional gate types from requirements: authority, risk, lockdown
            if gate.get("required_authority") and not gate.get("authority_session_active"):
                blocks.append("AUTHORITY_EXPIRED")
                actions.append(f"INJECT AUTHORITY SESSION FOR {h_id}")
                status.is_ready = False

            # 3. Risk Gate
            if h.risk_level in ["high", "critical"]:
                # High risk missions need explicit Creator session authority
                # (For now, we'll just flag them as needing 'Manual Review' if in a risk chain)
                if h_id in schedule.risk_chain:
                     blocks.append("RISK_CHAIN_HOLD")
                     actions.append("REVIEW TACTICAL SEQUENCE")
                     status.is_ready = False

            # 4. Surface Lock Gate (Check SystemState/Constitution)
            # This would integrate with a 'GlobalFreeze' check
            
            # Compute rationale
            if status.is_ready:
                status.rationale = "Constitucionalmente apto para lanzamiento."
                status.gate_color = "#32ff96"
            else:
                status.rationale = f"Retenido por: {', '.join(blocks)}. Acciones requeridas: {len(actions)}."
                status.gate_color = "#ff4444"
            
            status.blocks = blocks
            status.required_actions = actions
            audit_results[h_id] = status

        return audit_results

    def compute_optimized_sequence(self, schedule: MissionSchedule, handoffs: List[ProposedMission]) -> SequenceProposal:
        """
        CAPA 2: TOPOLOGICAL ANALYSIS ENGINE.
        Computes the most logical order based on dependencies, collisions and risk.
        """
        nodes = [h.handoff_id for h in handoffs]
        adj = {n: [] for n in nodes}
        in_degree = {n: 0 for n in nodes}
        
        # 1. Build Dependency Graph
        # Hard Dependencies from dependency_hints
        for h_id, hints in schedule.dependency_hints.items():
            for d in hints:
                if d["type"] == "IMPLICIT_DEPENDENCY":
                    u, v = d["depends_on"], h_id
                    if v not in adj[u]:
                        adj[u].append(v)
                        in_degree[v] += 1

        # 2. Add Weak Edges from Surface Collisions
        # If A and B collide, A should probably go before B (arbitrary choice but creates a flow)
        # to ensure the rebase pattern is followed.
        for h_id, conflicts in schedule.conflict_chain.items():
            for c in conflicts:
                if c["type"] == "SURFACE_COLLISION":
                    u, v = c["with_handoff"], h_id
                    if v not in adj[u] and u not in adj[v]: # Only if no direction exists
                         adj[u].append(v)
                         in_degree[v] += 1

        # 3. Kahn's Algorithm
        queue = [n for n in nodes if in_degree[n] == 0]
        # Sort initial queue by priority
        queue.sort(key=lambda n: next((h.priority for h in handoffs if h.handoff_id == n), 0), reverse=True)
        
        topo_order = []
        while queue:
            u = queue.pop(0)
            topo_order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # Cycle detection
        if len(topo_order) < len(nodes):
             return SequenceProposal(
                 suggested_order=schedule.ordered_handoff_ids,
                 confidence=0.3,
                 rationale="Ciclo de dependencias detectado. El reordenamiento automático no es seguro.",
                 cycles_detected=[nodes] # Simplified
             )

        # 4. Risk Decoupling (Post-Processing)
        # Try to insert low-risk buffers between consecutive high-risk nodes if possible
        final_order = []
        high_risk_ids = [h.handoff_id for h in handoffs if h.risk_level in ["high", "critical"]]
        low_risk_pool = [n for n in topo_order if n not in high_risk_ids]
        
        gaps = 0
        for i, n in enumerate(topo_order):
            final_order.append(n)
            # If this is high risk and the NEXT one is also high risk...
            if n in high_risk_ids and i + 1 < len(topo_order) and topo_order[i+1] in high_risk_ids:
                if low_risk_pool:
                     # This is a bit complex for a basic topo sort because moving a node
                     # might break a hard dependency. For now, we'll just flag it.
                     pass 

        return SequenceProposal(
            suggested_order=topo_order,
            confidence=0.9 if len(topo_order) == len(nodes) else 0.5,
            rationale="Secuencia optimizada para satisfacer dependencias críticas y minimizar colisiones de superficie."
        )

    def update_order(self, schedule_id: str, new_order: List[str]):
        schedule = self.get_schedule(schedule_id)
        if not schedule: return
        schedule.ordered_handoff_ids = new_order
        self._save(schedule)
        self.analyze_sequence(schedule_id)

    def analyze_reorder(self, schedule_id: str, proposed_order: List[str]) -> ReorderAnalysis:
        """
        CAPA 2: REORDER ANALYZER.
        Compares current schedule against a proposed order without persisting.
        """
        original = self.get_schedule(schedule_id)
        if not original: raise ValueError("Schedule not found")
        
        # Analyze current state (it might already be analyzed, but let's be sure)
        current = self.analyze_sequence(schedule_id)
        
        # Simulate proposed state
        import copy
        simulated = copy.deepcopy(current)
        simulated.ordered_handoff_ids = proposed_order
        
        # Run analysis without _save
        # We need a headless version of analyze_sequence logic or just pass a flag
        simulated = self._analyze_logic(simulated)
        
        # Compare
        analysis = ReorderAnalysis(
            group_id=schedule_id,
            previous_order=current.ordered_handoff_ids,
            proposed_order=proposed_order
        )
        
        # 1. Readiness Comparison
        curr_ready_count = len([v for v in current.launch_audit.values() if v.is_ready])
        sim_ready_count = len([v for v in simulated.launch_audit.values() if v.is_ready])
        
        analysis.improved_readiness = sim_ready_count > curr_ready_count
        analysis.readiness_delta = (sim_ready_count - curr_ready_count) / max(1, len(current.ordered_handoff_ids))
        
        # 2. Blockers Diff
        for h_id, sim_gate in simulated.launch_audit.items():
            curr_gate = current.launch_audit.get(h_id)
            if sim_gate.is_ready and (not curr_gate or not curr_gate.is_ready):
                analysis.newly_ready_ids.append(h_id)
            elif not sim_gate.is_ready and (curr_gate and curr_gate.is_ready):
                analysis.newly_blocked_ids.append(h_id)
                
        # 3. Dependency Check
        for h_id, hints in simulated.dependency_hints.items():
            for hint in hints:
                if hint.get("status") == "VIOLATED":
                    analysis.broken_dependencies.append({
                        "handoff_id": h_id,
                        "depends_on": hint["depends_on"],
                        "reason": hint["reason"]
                    })
        
        # 4. Rebase Pressure
        analysis.rebase_pressure_delta = len(simulated.rebase_required_flags) - len(current.rebase_required_flags)
        
        if analysis.rebase_pressure_delta < 0 or analysis.improved_readiness:
            analysis.risk_impact = "improved"
        elif analysis.rebase_pressure_delta > 0 or analysis.newly_blocked_ids:
            analysis.risk_impact = "worsened"
            
        return analysis

    def _analyze_logic(self, schedule: MissionSchedule) -> MissionSchedule:
        """Internal logic of analyze_sequence but without persistence."""
        handoffs = []
        for h_id in schedule.ordered_handoff_ids:
            h = handoff_manager.get_proposal(h_id)
            if h: handoffs.append(h)

        schedule.dependency_hints = {}
        schedule.risk_chain = {}
        schedule.conflict_chain = {}
        schedule.rebase_required_flags = []
        
        global_surface_map = {}
        for h in handoffs:
            for s in (h.surface_affected or []):
                if s not in global_surface_map: global_surface_map[s] = []
                global_surface_map[s].append(h.handoff_id)

        surface_owner = {} 
        for i, h_id in enumerate(schedule.ordered_handoff_ids):
            h = next((ho for ho in handoffs if ho.handoff_id == h_id), None)
            if not h: continue
            
            surfaces = h.surface_affected or []
            for s in surfaces:
                if s in surface_owner:
                    for prev_id in surface_owner[s]:
                        schedule.conflict_chain[h_id] = schedule.conflict_chain.get(h_id, [])
                        schedule.conflict_chain[h_id].append({"type": "SURFACE_COLLISION", "surface": s, "with_handoff": prev_id})
                        if h_id not in schedule.rebase_required_flags: schedule.rebase_required_flags.append(h_id)
                if s not in surface_owner: surface_owner[s] = []
                surface_owner[s].append(h_id)

        # Global dependencies
        for h in handoffs:
            for s, owners in global_surface_map.items():
                if s.lower() in h.objective.lower():
                    for owner in owners:
                        if owner != h.handoff_id:
                            idx_own = schedule.ordered_handoff_ids.index(owner)
                            idx_h = schedule.ordered_handoff_ids.index(h.handoff_id)
                            status = "SATISFIED" if idx_own < idx_h else "VIOLATED"
                            schedule.dependency_hints[h.handoff_id] = schedule.dependency_hints.get(h.handoff_id, [])
                            if not any(d["depends_on"] == owner for d in schedule.dependency_hints[h.handoff_id]):
                                schedule.dependency_hints[h.handoff_id].append({
                                    "type": "IMPLICIT_DEPENDENCY", "surface": s, "depends_on": owner, "status": status,
                                    "reason": f"Dependencia de {s} ({owner[:6]}) " + ("OK" if status == "SATISFIED" else "ERROR")
                                })

        schedule.launch_audit = self.audit_launch_readiness(schedule, handoffs)
        return schedule

    def update_schedule(self, schedule_id: str, updates: Dict[str, Any]):
        """General update for schedule metadata or status flags."""
        schedule = self.get_schedule(schedule_id)
        if schedule:
            for k, v in updates.items():
                if hasattr(schedule, k):
                    setattr(schedule, k, v)
            self._save(schedule)
            return schedule
        return None

scheduler_manager = SchedulerManager()
