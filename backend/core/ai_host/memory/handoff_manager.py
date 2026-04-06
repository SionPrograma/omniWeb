import uuid
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class ForeclosureAudit(BaseModel):
    status: str = "ACTIVE" # ACTIVE, CANDIDATE_FORECLOSE, CANDIDATE_ARCHIVE, FORECLOSED
    reason: str = ""
    evidence: List[str] = []
    confidence: float = 0.0
    superseded_by: Optional[str] = None
    duplicate_of: Optional[str] = None

class ProposedMission(BaseModel):
    handoff_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    briefing_title: str
    objective: str
    surface_affected: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    risk_level: str = "low"
    execution_style: str = "with_confirmation"
    readiness_state: str = "PENDING" # PENDING, READY, BLOCKED, DRAFT, ABORTED, ARCHIVED
    source_type: str = "chat"
    source_draft_id: Optional[str] = None # Traceability to Atlas draft
    gate_data: Optional[Dict[str, Any]] = None
    foreclosure: ForeclosureAudit = Field(default_factory=ForeclosureAudit)
    priority: int = 0
    origin_persona: str = "CREATOR_CORE"
    supporting_personas: List[str] = Field(default_factory=list)
    branch_id: str = "main"
    ancestry_id: Optional[str] = None # Original mission ID this was cloned from
    governance_rebase: Optional[List[Dict[str, Any]]] = None # Rebase Advisory info
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        return cls(
            handoff_id=row["handoff_id"],
            briefing_title=row["briefing_title"],
            objective=row["objective"],
            surface_affected=json.loads(row["surface_affected"]) if isinstance(row["surface_affected"], str) else (row["surface_affected"] or []),
            constraints=json.loads(row["constraints"]) if isinstance(row["constraints"], str) else (row["constraints"] or []),
            risk_level=row["risk_level"],
            execution_style=row["execution_style"],
            readiness_state=row["readiness_state"],
            source_type=row["source_type"],
            gate_data=json.loads(row["gate_data"]) if row["gate_data"] and isinstance(row["gate_data"], str) else (row["gate_data"] or None),
            foreclosure=ForeclosureAudit(**json.loads(row["foreclosure"])) if row["foreclosure"] and isinstance(row["foreclosure"], str) else (row["foreclosure"] or ForeclosureAudit()),
            priority=row["priority"],
            origin_persona=row["origin_persona"] if "origin_persona" in row.keys() else "CREATOR_CORE",
            supporting_personas=json.loads(row["supporting_personas"]) if "supporting_personas" in row.keys() and row["supporting_personas"] else [],
            branch_id=row["branch_id"] if "branch_id" in row.keys() else "main",
            source_draft_id=row.get("source_draft_id"),
            ancestry_id=row.get("ancestry_id"),
            governance_rebase=None, # Loaded separately if needed
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"]
        )

class HandoffManager:
    """
    Manages the backlog of proposed missions (Handoffs) before they are executed.
    Ensures the Creator can manage multiple intents without losing context.
    """
    
    def add_proposal(self, mission_dict: Dict[str, Any], gate: Optional[Dict[str, Any]] = None, source: str = "chat") -> ProposedMission:
        """Adds a new mission proposal to the handoff queue."""
        
        # Determine initial state
        state = "PENDING"
        if gate and gate.get("required"):
            state = "BLOCKED" if gate.get("type") == "PIN" else "READY"
        
        proposal = ProposedMission(
            briefing_title=f"Misión: {mission_dict.get('objective', 'Sin Título')[:40]}...",
            objective=mission_dict.get("objective", ""),
            surface_affected=mission_dict.get("surface_affected", []),
            constraints=mission_dict.get("constraints", []),
            risk_level=mission_dict.get("risk_level", "low"),
            execution_style=mission_dict.get("execution_style", "with_confirmation"),
            readiness_state=state,
            source_type=source,
            source_draft_id=mission_dict.get("source_draft_id"),
            gate_data=gate,
            origin_persona=mission_dict.get("origin_persona", "CREATOR_CORE"),
            supporting_personas=mission_dict.get("supporting_personas", [])
        )
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO mission_handoffs (
                        handoff_id, briefing_title, objective, surface_affected, 
                        constraints, risk_level, execution_style, readiness_state, 
                        source_type, source_draft_id, gate_data, foreclosure, priority, origin_persona, 
                        supporting_personas, branch_id, ancestry_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal.handoff_id, proposal.briefing_title, proposal.objective,
                    json.dumps(proposal.surface_affected), json.dumps(proposal.constraints),
                    proposal.risk_level, proposal.execution_style, proposal.readiness_state,
                    proposal.source_type, proposal.source_draft_id, json.dumps(proposal.gate_data) if proposal.gate_data else None,
                    json.dumps(proposal.foreclosure.model_dump()),
                    proposal.priority, proposal.origin_persona, json.dumps(proposal.supporting_personas),
                    proposal.branch_id, proposal.ancestry_id or proposal.handoff_id
                ))
                conn.commit()
                
        logger.info(f"MISSION HANDOFF: Saved proposal {proposal.handoff_id} from {source}")
        return proposal

    def get_all(self, include_archived: bool = False, branch_id: str = "main", conn: Optional[sqlite3.Connection] = None, load_rebase: bool = True) -> List[ProposedMission]:
        """Returns all active proposals for a specific branch."""
        with set_chip_context("core"):
            if conn:
                return self._execute_get_all(conn, include_archived, branch_id, load_rebase)
            else:
                with db_manager.get_connection() as new_conn:
                    return self._execute_get_all(new_conn, include_archived, branch_id, load_rebase)

    def _execute_get_all(self, conn, include_archived, branch_id, load_rebase):
        query = "SELECT * FROM mission_handoffs WHERE branch_id = ?"
        if not include_archived:
            query += " AND readiness_state != 'ARCHIVED'"
        rows = conn.execute(f"{query} ORDER BY priority DESC, created_at DESC", (branch_id,)).fetchall()
        proposals = [ProposedMission.from_row(dict(row)) for row in rows]
        
        # Load structural rebase recommendations
        if load_rebase:
            try:
                from .branch_manager import branch_manager
                rebase_ads = branch_manager.get_mission_rebase_recommendations(branch_id=branch_id, load_handoffs=False)
                for p in proposals:
                    p.governance_rebase = [r for r in rebase_ads if r["affected_handoff_id"] == p.handoff_id]
            except Exception as e:
                logger.error(f"Failed to attach rebase advisories to handoffs: {e}")
            
        return proposals

    def get_proposal(self, handoff_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[ProposedMission]:
        with set_chip_context("core"):
            if conn:
                return self._execute_get_proposal(conn, handoff_id)
            else:
                with db_manager.get_connection() as new_conn:
                    return self._execute_get_proposal(new_conn, handoff_id)

    def _execute_get_proposal(self, conn, handoff_id):
        row = conn.execute("SELECT * FROM mission_handoffs WHERE handoff_id = ?", (handoff_id,)).fetchone()
        if row:
            return ProposedMission.from_row(dict(row))
        return None

    def update_proposal(self, handoff_id: str, updates: Dict[str, Any]):
        """Updates proposal fields (e.g. status, priority, objective)."""
        if not updates: return
        
        fields = []
        values = []
        for k, v in updates.items():
            fields.append(f"{k} = ?")
            if hasattr(v, "model_dump"):
                values.append(json.dumps(v.model_dump()))
            elif isinstance(v, (list, dict)):
                values.append(json.dumps(v))
            else:
                values.append(v)
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(handoff_id)
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(f"UPDATE mission_handoffs SET {', '.join(fields)} WHERE handoff_id = ?", tuple(values))
                conn.commit()

    def delete_proposal(self, handoff_id: str):
        """Removes a mission proposal from the system."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM mission_handoffs WHERE handoff_id = ?", (handoff_id,))
                conn.commit()

    def check_rebase(self, handoff_id: str) -> Dict[str, Any]:
        """
        CAPA 2 (PHASE 87): REBASE ENGINE.
        Taxonomía: STILL_VALID, NEEDS_REFRESH, CONFLICTED, BLOCKED_BY_STATE, OBSOLETE.
        """
        proposal = self.get_proposal(handoff_id)
        if not proposal:
            return {"status": "NOT_FOUND"}
            
        surfaces = proposal.surface_affected
        objective = proposal.objective
        creation_time = proposal.created_at.isoformat()
        
        rebase_report = {
            "handoff_id": handoff_id,
            "status": "STILL_VALID",
            "detected_changes": [],
            "conflicts": [],
            "suggested_update": None,
            "rebase_confidence": 1.0,
            "original_snapshot": {"created_at": creation_time, "risk": proposal.risk_level},
            "current_system_snapshot": {"checked_at": datetime.now().isoformat()}
        }
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. OBSOLETE Check: Has an identical mission already completed?
                try:
                    similar_completed = conn.execute("""
                        SELECT mission_id, message, timestamp 
                        FROM system_mission_telemetry 
                        WHERE event_type = 'MISSION_COMPLETED'
                        AND message LIKE ?
                        AND timestamp > ?
                    """, (f"%{objective}%", creation_time)).fetchone()
                    
                    if similar_completed:
                        rebase_report["status"] = "OBSOLETE"
                        rebase_report["detected_changes"].append({
                            "type": "REDUNDANCY",
                            "detail": f"Misión idéntica ya completada el {similar_completed['timestamp']}"
                        })
                        rebase_report["rebase_confidence"] = 0.1
                except: pass

                # 2. SURFACE MUTATIONS (NEEDS_REFRESH)
                if rebase_report["status"] != "OBSOLETE" and surfaces:
                    placeholders = ', '.join(['?'] * len(surfaces))
                    try:
                        mutations = conn.execute(f"""
                            SELECT mutation_type, module_name, timestamp 
                            FROM builder_mutations 
                            WHERE module_name IN ({placeholders}) 
                            AND timestamp > ?
                        """, tuple(surfaces) + (creation_time,)).fetchall()
                        
                        for m in mutations:
                            rebase_report["detected_changes"].append({
                                "type": "SURFACE_MUTATION",
                                "target": m["module_name"],
                                "detail": f"Cambio externo en {m['module_name']} detectado.",
                                "ts": m["timestamp"]
                            })
                            rebase_report["status"] = "NEEDS_REFRESH"
                    except: pass

                # 3. RESOURCE LOCKS (CONFLICTED)
                try:
                    locks = conn.execute("SELECT resource_key, reason FROM system_locks").fetchall()
                    for l in locks:
                        if l["resource_key"] in surfaces:
                            rebase_report["conflicts"].append(f"Bloqueo activo en '{l['resource_key']}': {l['reason']}")
                            rebase_report["status"] = "CONFLICTED"
                except: pass

                # 4. GOVERNANCE DRIFT (BLOCKED_BY_STATE)
                # Check for global 'audit_lock' or high-risk surface freeze
                try:
                    global_lock = conn.execute("SELECT * FROM system_locks WHERE resource_key = 'global_governance'").fetchone()
                    if global_lock:
                        rebase_report["status"] = "BLOCKED_BY_STATE"
                        rebase_report["conflicts"].append(f"Sistema bajo bloqueo de gobernanza global: {global_lock['reason']}")
                except: pass

        if rebase_report["status"] in ["CONFLICTED", "BLOCKED_BY_STATE"]:
             rebase_report["rebase_confidence"] = 0.2
        elif rebase_report["status"] == "NEEDS_REFRESH":
             rebase_report["rebase_confidence"] = 0.6
             
        return rebase_report

    def audit_foreclosure(self) -> List[ProposedMission]:
        """
        CAPA 2: STRATEGIC FORECLOSURE ENGINE.
        Analiza el backlog buscando misiones obsoletas o duplicadas.
        """
        all_missions = self.get_all(include_archived=False)
        pending = [m for m in all_missions if m.readiness_state in ["PENDING", "BLOCKED", "DRAFT"]]
        
        surface_active = {} # surface -> Mission
        
        for m in pending:
            audit = ForeclosureAudit(status="ACTIVE")
            evidence = []
            
            # 1. OBSOLETE CHECK (Via Rebase Engine)
            rebase = self.check_rebase(m.handoff_id)
            if rebase["status"] == "OBSOLETE":
                audit.status = "CANDIDATE_FORECLOSE"
                audit.reason = "Misión obsoleta: El objetivo ya ha sido cumplido por una ejecución previa."
                evidence.append(f"Detectado por Rebase Engine: {rebase['detected_changes'][0]['detail']}")
                audit.confidence = 0.95
            
            # 2. DUPLICATE/SUPERSEDED CHECK (Semantic Surface Overlap)
            for s in m.surface_affected:
                if s in surface_active:
                    prev = surface_active[s]
                    # If this is newer and overlaps semantically
                    if m.created_at > prev.created_at:
                        # Simple semantic overlap check (placeholder for LLM pass)
                        overlap_score = 0.0
                        if any(word in prev.objective.lower() for word in m.objective.lower().split() if len(word) > 4):
                            overlap_score = 0.7
                        
                        if overlap_score > 0.6:
                             # This mission might supersede the previous one
                             prev_audit = prev.foreclosure
                             prev_audit.status = "CANDIDATE_ARCHIVE"
                             prev_audit.reason = f"Superada por misión más reciente: {m.handoff_id[:6]}"
                             prev_audit.superseded_by = m.handoff_id
                             prev_audit.confidence = 0.8
                             self.update_proposal(prev.handoff_id, {"foreclosure": prev_audit})
                
                surface_active[s] = m

            if audit.status != "ACTIVE":
                audit.evidence = evidence
                self.update_proposal(m.handoff_id, {"foreclosure": audit})
        
        return self.get_all()

    def foreclose_proposal(self, handoff_id: str, reason: str, action_type: str = "FORECLOSE"):
        """
        CAPA 4: ATOMIC ACTION FLOW.
        Aplica el cierre formal de una propuesta.
        """
        proposal = self.get_proposal(handoff_id)
        if not proposal: return
        
        audit = proposal.foreclosure
        audit.status = "FORECLOSED" if action_type == "FORECLOSE" else "ARCHIVED"
        audit.reason = reason
        
        new_state = "ARCHIVED" # Both foreclose/archive move out of active queue
        self.update_proposal(handoff_id, {
            "readiness_state": new_state,
            "foreclosure": audit
        })
        logger.info(f"FORECLOSURE: Mission {handoff_id} closed as {action_type}. Reason: {reason}")

    def reactivate_handoff(self, handoff_id: str):
        """Devuelve una misión cerrada a la cola activa."""
        proposal = self.get_proposal(handoff_id)
        if not proposal: return
        
        audit = proposal.foreclosure
        audit.status = "ACTIVE"
        audit.reason = "Reactivado por el creador."
        
        self.update_proposal(handoff_id, {
            "readiness_state": "PENDING",
            "foreclosure": audit
        })
        logger.info(f"FORECLOSURE: Mission {handoff_id} reactivated.")

handoff_manager = HandoffManager()
