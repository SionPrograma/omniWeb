import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.core.ai_host.memory.handoff_manager import handoff_manager, ProposedMission

logger = logging.getLogger(__name__)

class SynergyInsight(BaseModel):
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handoff_a: str
    handoff_b: str
    relation_type: str # EXACT_DUPLICATE, NEAR_DUPLICATE, SURFACE_OVERLAP, GOAL_OVERLAP, SUBSUMED_BY
    score: float # 0.0 to 1.0
    rationale: str
    suggested_action: str # MERGE, ARCHIVE_B, SUPERSEDE_A, KEEP_SEPARATE
    keep_separate_reason: Optional[str] = None
    composite_preview: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)

class SynergyManager:
    """
    CAPA 1 & 2: MISSION SYNERGY & REDUNDANCY PURGE.
    Detects clusters of missions that should be fused or archived.
    """
    
    def analyze_backlog(self, schedule_id: Optional[str] = None) -> List[SynergyInsight]:
        """Runs a full backlog analysis to find synergies."""
        all_missions = handoff_manager.get_all(include_archived=False)
        pending = [m for m in all_missions if m.readiness_state in ["PENDING", "BLOCKED", "DRAFT", "READY"]]
        
        insights = []
        processed_pairs = set()
        
        for i, m_a in enumerate(pending):
            for j, m_b in enumerate(pending):
                if i >= j: continue # Avoid duplicate pairs and self-comparison
                
                pair_key = tuple(sorted([m_a.handoff_id, m_b.handoff_id]))
                if pair_key in processed_pairs: continue
                processed_pairs.add(pair_key)
                
                insight = self._compute_relation(m_a, m_b)
                if insight:
                    insights.append(insight)
        
        return insights

    def _compute_relation(self, m_a: ProposedMission, m_b: ProposedMission) -> Optional[SynergyInsight]:
        """Internal heuristic for synergy detection."""
        
        # 1. Surface Overlap (Jaccard)
        s_a = set(m_a.surface_affected or [])
        s_b = set(m_b.surface_affected or [])
        
        union = s_a | s_b
        intersection = s_a & s_b
        
        surface_score = len(intersection) / len(union) if union else 0.0
        
        # 2. Goal Overlap (Token intersection - simplified)
        words_a = set([w for w in m_a.objective.lower().split() if len(w) > 4])
        words_b = set([w for w in m_b.objective.lower().split() if len(w) > 4])
        
        goal_union = words_a | words_b
        goal_intersection = words_a & words_b
        goal_score = len(goal_intersection) / len(goal_union) if goal_union else 0.0
        
        # 3. Decision Logic
        relation_type = None
        suggested_action = "KEEP_SEPARATE"
        score = max(surface_score, goal_score)
        rationale = ""
        
        # EXACT DUPLICATE
        if surface_score > 0.9 and goal_score > 0.8:
            relation_type = "EXACT_DUPLICATE"
            suggested_action = "ARCHIVE_B"
            rationale = "Misiones idénticas detectadas."
        
        # SUBSUMED_BY (A inside B)
        elif s_a.issubset(s_b) and words_a.issubset(words_b) and len(s_b) > len(s_a):
            relation_type = "SUBSUMED_BY"
            suggested_action = "SUPERSEDE_A"
            rationale = f"Misión {m_a.handoff_id[:6]} está contenida en {m_b.handoff_id[:6]}."
            
        # NEAR DUPLICATE / MERGE CANDIDATE
        elif surface_score > 0.4 or goal_score > 0.3:
            relation_type = "MERGE_CANDIDATE"
            suggested_action = "MERGE"
            rationale = "Superposición táctica detectada. Fusión recomendada para simplificar el roadmap."
            
        if not relation_type or score < 0.2:
            return None

        # 4. Safety Constraints (Governance/Risk)
        keep_separate = False
        separate_reason = ""
        
        # Mix of High/Low Risk
        if m_a.risk_level != m_b.risk_level:
            keep_separate = True
            separate_reason = f"RIESGO INCOMPATIBLE ({m_a.risk_level.upper()} vs {m_b.risk_level.upper()})."
        
        # Mix of different governance gates
        gate_a = m_a.gate_data or {}
        gate_b = m_b.gate_data or {}
        if gate_a.get("type") != gate_b.get("type"):
            keep_separate = True
            separate_reason = "CONTRATOS DE GOBERNANZA DIVERGENTES (Requiere revisión manual)."
            
        if keep_separate:
            suggested_action = "KEEP_SEPARATE"
            rationale = f"Mantener separadas: {separate_reason} " + rationale
            
        # 5. Composite Preview
        preview = None
        if suggested_action == "MERGE":
            preview = {
                "briefing_title": f"FUSIÓN: {m_a.briefing_title[:15]} + {m_b.briefing_title[:15]}",
                "objective": f"{m_a.objective}\n\nREFINAMIENTO ADICIONAL:\n{m_b.objective}",
                "surface_affected": list(union),
                "constraints": list(set(m_a.constraints or []) | set(m_b.constraints or [])),
                "risk_level": "high" if "high" in [m_a.risk_level, m_b.risk_level] else "low"
            }
            
        return SynergyInsight(
            handoff_a=m_a.handoff_id,
            handoff_b=m_b.handoff_id,
            relation_type=relation_type,
            score=score,
            rationale=rationale,
            suggested_action=suggested_action,
            keep_separate_reason=separate_reason if keep_separate else None,
            composite_preview=preview
        )

    def apply_insight(self, insight: SynergyInsight):
        """Applies the suggested action from an insight."""
        if insight.suggested_action == "ARCHIVE_B":
            handoff_manager.foreclose_proposal(insight.handoff_b, f"Cierre por redundancia con {insight.handoff_a[:6]}: {insight.rationale}", "ARCHIVE")
            
        elif insight.suggested_action == "SUPERSEDE_A":
            handoff_manager.foreclose_proposal(insight.handoff_a, f"Superada por {insight.handoff_b[:6]}: {insight.rationale}", "ARCHIVE")
            
        elif insight.suggested_action == "MERGE":
            if not insight.composite_preview: return
            
            # Create new composite
            new_mission = handoff_manager.add_proposal(insight.composite_preview, source="synergy_merge")
            
            # Archive originals
            handoff_manager.foreclose_proposal(insight.handoff_a, f"Fusionada en nueva misión {new_mission.handoff_id[:6]}", "ARCHIVE")
            handoff_manager.foreclose_proposal(insight.handoff_b, f"Fusionada en nueva misión {new_mission.handoff_id[:6]}", "ARCHIVE")
            
            # Link originals to new one in forensic data (optional but good)
            current_a = handoff_manager.get_proposal(insight.handoff_a)
            if current_a:
                f = current_a.foreclosure
                f.superseded_by = new_mission.handoff_id
                handoff_manager.update_proposal(insight.handoff_a, {"foreclosure": f})
                
            current_b = handoff_manager.get_proposal(insight.handoff_b)
            if current_b:
                f = current_b.foreclosure
                f.superseded_by = new_mission.handoff_id
                handoff_manager.update_proposal(insight.handoff_b, {"foreclosure": f})
            
            return new_mission
            
synergy_manager = SynergyManager()
