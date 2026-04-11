import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class MissionDraft(BaseModel):
    draft_id: str
    source_node_id: str
    draft_type: str
    title: str
    objective: str
    surface_affected: List[str]
    constraints: List[str]
    preconditions: List[str]
    risk_level: str
    confidence: float
    rationale: str
    catalyst_assisted: bool = False
    catalyst_trace_id: Optional[str] = None
    steps: List[Dict[str, Any]] = []

class MissionDraftEngine:
    """
    Transforms Wisdom Suggestions into actionable Mission Drafts.
    """
    def __init__(self):
        self.draft_types = {
            "CAUTIONARY_PATTERN": "PREVENTIVE_ADVISORY_DRAFT",
            "REUSABLE_TACTIC": "RELIEF_MISSION_DRAFT",
            "HIGH_RELEVANCE_WISDOM": "SAFE_REFACTOR_DRAFT",
            "ROOT_CAUSE_FINDING": "ROOT_AUDIT_DRAFT",
            "OVER_ENGINEERING_PATTERN": "SCOPE_REDUCTION_DRAFT",
            "EXPERIMENTAL_REFERENCE": "EXPERIMENTAL_BRANCH_DRAFT"
        }

    def create_draft_from_suggestion(self, suggestion: Dict[str, Any], context: Dict[str, Any]) -> MissionDraft:
        """Translates advice into a structured mission contract."""
        
        s_type = suggestion.get("reasoning_type", "EXPERIMENTAL_REFERENCE")
        draft_type = self.draft_types.get(s_type, "EXPERIMENTAL_BRANCH_DRAFT")
        
        # Build Title/Objective
        node_title = suggestion.get("title", "Wisdom Node")
        title = f"Intervención: {node_title}"
        objective = f"Aplicar sabiduría contextual: {suggestion.get('rationale', '')}"
        
        # PHASE 121: Catalyst Acceleration Attempt (Format Synthesis)
        from backend.core.governance.catalyst_engine import catalyst_engine
        catalyst_res = catalyst_engine.execute_formatting_task({
            "objective": objective,
            "context_text": f"Rationale: {suggestion.get('rationale')}. Domain: {context.get('target_domain')}",
            "tactic_id": suggestion.get("node_id")
        })

        assisted = False
        trace_id = None
        if catalyst_res:
            objective = catalyst_res.get("objective", objective)
            assisted = True
            trace_id = catalyst_res.get("catalyst_trace_id")
            logger.info(f"Draft {title} accelerated by catalyst {trace_id}")
        
        # Extract Constraints/Preconditions from Reasoner output or Origin Node?
        # For now, we use standard logic based on type.
        constraints = [
            "No mutar estado global sin snapshot previo.",
            "Validar impacto en hotspots de dominio."
        ]
        if s_type == "CAUTIONARY_PATTERN":
            constraints.append("Abortar si se detecta degradación de memoria (evitar patrón de fallo).")
        
        preconditions = [
            f"Fricción de dominio '{context.get('target_domain', 'global')}' < 80%",
            "Conexión con Gobernanza nominal."
        ]

        # Risk Mapping
        risk = "MEDIUM"
        if s_type == "CAUTIONARY_PATTERN": risk = "HIGH"
        if s_type == "EXPERIMENTAL_REFERENCE": risk = "LOW"

        draft = MissionDraft(
            draft_id=f"DRAFT-{uuid.uuid4().hex[:8]}",
            source_node_id=suggestion.get("node_id", "unknown"),
            draft_type=draft_type,
            title=title,
            objective=objective,
            surface_affected=suggestion.get("affected_domains", context.get("target_domain", "global")).split(',') if isinstance(suggestion.get("affected_domains"), str) else [context.get("target_domain", "global")],
            constraints=constraints,
            preconditions=preconditions,
            risk_level=risk,
            confidence=suggestion.get("confidence", 0.5),
            rationale=suggestion.get("rationale", "Generación nativa."),
            catalyst_assisted=assisted,
            catalyst_trace_id=trace_id,
            steps=catalyst_res.get("steps", []) if catalyst_res else []
        )
        
        self._persist_draft(draft, suggestion.get("suggestion_id", "manual"), context)
        return draft

    def _persist_draft(self, draft: MissionDraft, suggestion_id: str, context: Dict[str, Any]):
        with set_chip_context("governance"):
            with db_manager.get_connection() as conn:
                try:
                    conn.execute("""
                        INSERT INTO governance_mission_auto_drafts (
                            draft_id, source_reasoner_result_id, source_atlas_node_ref, 
                            draft_type, target_context_ref, title_suggestion, 
                            objective_suggestion, affected_domains, rationale, 
                            suggested_constraints, recommended_preconditions, risk_notes, 
                            confidence, suggested_steps, catalyst_trace_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        draft.draft_id, suggestion_id, draft.source_node_id,
                        draft.draft_type, json.dumps(context), draft.title,
                        draft.objective, json.dumps(draft.surface_affected), draft.rationale,
                        json.dumps(draft.constraints), json.dumps(draft.preconditions), 
                        f"Generated as {draft.risk_level}", draft.confidence,
                        json.dumps(draft.steps), draft.catalyst_trace_id
                    ))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Draft persistence failed: {e}")

draft_engine = MissionDraftEngine()
