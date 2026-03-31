from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from ..cognition.cognitive_core import cognitive_core
from ..reasoning.evidence_engine import evidence_engine
from ..learning.adaptive_learning import adaptive_learning

class DeliberationContext(BaseModel):
    user_intent: str
    normalized_request: str
    source_surface: str = "chat"
    recent_topic: Optional[str] = None
    semantic_memory_matches: List[Dict[str, Any]] = []
    system_world_state: Dict[str, Any] = {}
    relevant_evidence: List[Dict[str, Any]] = []
    active_hypotheses: List[Dict[str, Any]] = []
    recent_execution_history: List[Dict[str, Any]] = []
    learning_signals: Dict[str, Any] = {}
    engineering_memory_matches: List[Dict[str, Any]] = []
    relevant_chip_context: List[str] = []
    uncertainty_level: float = 0.0
    reasoning_mode: str = "conversational"
    evidence_bundle: Optional[Any] = None # Preservar el objeto original para el router
    active_mission: Optional[Dict[str, Any]] = None # Persistence Anchor


class DeliberationEngine:
    """
    Assembles a high-density cognitive context for Omni's reasoning host.
    Transforms raw messages into grounded deliberation contexts.
    """
    
    def __init__(self):
        self.default_uncertainty = 0.5

    async def assemble_context(self, normalized_request: str, intent: str, session_id: str, source_surface: str = "chat") -> DeliberationContext:
        # 1. Gather World State & Evidence
        ws = cognitive_core.world_state
        evidence_bundle = await evidence_engine.collect_evidence()
        from ..memory.mission_manager import mission_manager
        active_mission = mission_manager.get_active_mission()
        
        # 2. Pull Learning & Engineering History
        learning_report = adaptive_learning.get_reliability_report()
        history = [h.dict() for h in cognitive_core.execution_history[-10:]]
        
        # 3. Determine recent topic
        recent_topic = cognitive_core.get_recent_topic()
        
        # 4. Map hypotheses (Keep objects for inner calculation, serialize later)
        raw_hypotheses = self.get_active_hypotheses_raw()
        
        # 5. Calculate global uncertainty
        uncertainty = self._calculate_uncertainty(evidence_bundle, raw_hypotheses)
 
        evidence_list = [i.to_dict() for i in evidence_bundle.items]
        hypotheses_list = []
        for h in raw_hypotheses:
            if hasattr(h, 'dict'):
                hypotheses_list.append(h.dict())
            else:
                hypotheses_list.append(h.to_dict() if hasattr(h, 'to_dict') else vars(h))
 
        return DeliberationContext(
            user_intent=intent,
            normalized_request=normalized_request,
            source_surface=source_surface,
            recent_topic=recent_topic,
            system_world_state=ws.dict() if hasattr(ws, 'dict') else ws.to_dict(),
            relevant_evidence=evidence_list,
            active_hypotheses=hypotheses_list,
            recent_execution_history=history,
            learning_signals=learning_report.get("top_patterns", {}),
            relevant_chip_context=ws.active_chips,
            uncertainty_level=uncertainty,
            reasoning_mode=self._select_mode(intent, uncertainty, {"relevant_evidence": evidence_list, "request": normalized_request}),
            evidence_bundle=evidence_bundle,
            active_mission=active_mission.model_dump() if (active_mission and hasattr(active_mission, 'model_dump')) else (vars(active_mission) if active_mission else None)
        )


    def get_active_hypotheses_raw(self):
        """Helper to get raw hypotheses for internal calculation."""
        return [h for h in cognitive_core.hypotheses.values() if h.status == "active"]

    def _calculate_uncertainty(self, bundle, hypotheses) -> float:
        if not bundle.items:
            return 1.0
        if not hypotheses:
            return 0.7
        
        # Base confidence from highest hypothesis
        max_conf = max([h.confidence for h in hypotheses]) if hypotheses else 0.0
        return round(1.0 - max_conf, 2)

    def _select_mode(self, intent: str, uncertainty: float, context_data: Optional[Dict[str, Any]] = None) -> str:
        # Check for anomalies that trigger remediation
        has_anomalies = False
        if context_data and context_data.get('relevant_evidence'):
             # Trigger if any evidence indicates an issue
             for e in context_data['relevant_evidence']:
                 if "latency" in str(e.get("key")).lower() and e.get("value", 0) > 400:
                     has_anomalies = True
                 if "error" in str(e.get("key")).lower() or "fail" in str(e.get("key")).lower():
                     has_anomalies = True

        if intent in ["remediation", "healing", "REMEDIATION_INTENT"] or (intent in ["diagnostic", "analyze", "ANALYSIS_INTENT"] and has_anomalies):
            return "remediation"
            
        if intent in ["diagnostic", "analyze", "ANALYSIS_INTENT"]:
            return "reflective" if uncertainty > 0.4 else "diagnostic"
            
        if intent == "patch_proposal":
            return "patch_proposal"
        
        # Swarm Orchestration for complex creation/evolution tasks
        if intent == "BUILD_INTENT" or intent == "creator_plan":
             return "swarm_orchestration"

        if intent == "planning":
            return "planning"
        if uncertainty > 0.8 and intent not in ["CONVERSATIONAL_INTENT", "FOLLOW_UP_INTENT"]:
            return "limitation"
            
        return "conversational"

deliberation_engine = DeliberationEngine()
