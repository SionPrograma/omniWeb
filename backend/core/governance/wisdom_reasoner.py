import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.governance.atlas_engine import atlas_engine
from backend.core.governance.graph_engine import graph_engine

logger = logging.getLogger(__name__)

class WisdomSuggestion(BaseModel):
    suggestion_id: str
    node_id: str
    node_type: str
    title: str
    reasoning_type: str # HIGH_RELEVANCE_WISDOM, CAUTIONARY_PATTERN, etc.
    match_score: float
    confidence: float
    rationale: str
    recommended_use: str
    supporting_evidence: List[str] = []

class WisdomReasoner:
    """
    OMNIWEB — BLOQUE: TACTICAL WISDOM REASONER.
    Active reasoning layer that connects current context with tactical memory.
    """
    def __init__(self):
        self.taxonomies = {
            "HIGH": "HIGH_RELEVANCE_WISDOM",
            "WARN": "CAUTIONARY_PATTERN",
            "TACTIC": "REUSABLE_TACTIC",
            "REF": "EXPERIMENTAL_REFERENCE",
            "LOW": "INSUFFICIENT_REASONING_CONFIDENCE"
        }

    def analyze_context(self, context_data: Dict[str, Any]) -> List[WisdomSuggestion]:
        """
        Runs reasoning over atlas nodes based on current mission/branch/chat.
        Expected context_data: { "target_domain": str, "problem_type": str, "risk_level": str, ... }
        """
        with set_chip_context("core"):
            nodes = atlas_engine.get_nodes()
            suggestions = []

            for node in nodes:
                score, rationale_parts = self._calculate_relevance(node, context_data)
                
                if score > 0.4: # Only suggest if there's a reason
                    suggestion_type = self._classify_suggestion(node, score)
                    
                    suggestions.append(WisdomSuggestion(
                        suggestion_id=f"SUG-{uuid.uuid4().hex[:8]}",
                        node_id=node.node_id,
                        node_type=node.node_type,
                        title=node.title,
                        reasoning_type=suggestion_type,
                        match_score=score,
                        confidence=node.confidence,
                        rationale=" + ".join(rationale_parts),
                        recommended_use=self._get_recommendation(node, suggestion_type),
                        supporting_evidence=list(node.evidence_refs.keys())
                    ))

            # Prioritize and Limit
            suggestions.sort(key=lambda x: x.match_score, reverse=True)
            final_suggestions = suggestions[:5] # Max 5 for low noise
            
            self._log_reasoning_session(context_data, final_suggestions)
            return final_suggestions

    def _calculate_relevance(self, node: Any, context: Dict[str, Any]) -> (float, List[str]):
        """Detailed scoring logic."""
        score = 0.0
        parts = []

        # 1. Domain Match (Highest weight)
        target_domain = context.get("target_domain", "").lower()
        node_domains = [d.lower() for d in node.affected_domains]
        if target_domain and target_domain in node_domains:
            score += 0.5
            parts.append(f"Match de dominio ({target_domain})")

        # 2. Similarity of Problem Type
        p_type = context.get("problem_type", "").lower()
        if p_type and (p_type in node.title.lower() or p_type in node.summary.lower()):
            score += 0.3
            parts.append(f"Patrón detectado en {node.node_type.lower()}")

        # 3. High Reusability Bonus
        if node.reusability_score > 0.8:
            score += 0.1
            parts.append("Alta reutilización histórica")

        # 4. Confirmation Weight
        if node.status_band == "CONFIRMED":
            score += 0.1
            parts.append("Precedente validado")
        elif node.status_band == "CONTRADICTED_BY_REALITY":
            score += 0.2 # Higher visibility but as negative
            parts.append("Patrón de advertencia (contradicho)")

        return min(score, 1.0), parts

    def _classify_suggestion(self, node: Any, score: float) -> str:
        if node.status_band == "CONTRADICTED_BY_REALITY":
            return self.taxonomies["WARN"]
        if score > 0.8:
            return self.taxonomies["HIGH"]
        if node.node_type == "LEARNING" and node.reusability_score > 0.7:
            return self.taxonomies["TACTIC"]
        if node.status_band == "EXPERIMENTAL":
            return self.taxonomies["REF"]
        return self.taxonomies["LOW"]

    def _get_recommendation(self, node: Any, s_type: str) -> str:
        if s_type == self.taxonomies["WARN"]:
            return "Evitar este patrón o aplicar mitigación estricta."
        if s_type == self.taxonomies["HIGH"]:
            return "Revisar autopsia/learning fuente antes de proceder."
        if s_type == self.taxonomies["TACTIC"]:
            return "Considerar aplicar esta táctica directamente."
        return "Usar solo como referencia contextual."

    def _log_reasoning_session(self, context: Dict[str, Any], suggestions: List[WisdomSuggestion]):
        """Traceability: Logs what the reasoner suggested."""
        with db_manager.get_connection() as conn:
            session_id = f"RSESS-{uuid.uuid4().hex[:8]}"
            try:
                # Basic logging to a trace table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS governance_reasoner_traces (
                        trace_id TEXT PRIMARY KEY,
                        context_json TEXT,
                        suggestions_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    INSERT INTO governance_reasoner_traces (trace_id, context_json, suggestions_json)
                    VALUES (?, ?, ?)
                """, (session_id, json.dumps(context), json.dumps([s.model_dump() for s in suggestions])))
                conn.commit()
            except Exception as e:
                logger.error(f"Trace logging failed: {e}")

wisdom_reasoner = WisdomReasoner()
