import logging
import json
from typing import List, Dict, Any, Optional
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class CrossProjectSearchEngine:
    """
    OMNIWEB — BLOQUE: CROSS-PROJECT LEARNING SEARCH.
    Searches and recovers tactical learnings from other projects based on contextual similarity.
    """
    def __init__(self):
        self.current_project_id = "PROJECT_OMNIWEB_PROD"

    async def search_learnings(self, domain: str = None, problem_type: str = None, rationale_keywords: str = None) -> List[Dict[str, Any]]:
        """
        Executes a contextual search across projects for relevant learnings, autopsies and ledger records.
        """
        results = []
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                # 1. Fetch contextual mappings for project-level similarity
                mappings_res = await session.execute("SELECT * FROM governance_contextual_mappings WHERE target_project_id = ?", (self.current_project_id,))
                project_similarities = {r["source_project_id"]: r["similarity_score"] for r in mappings_res}
                
                # 2. Search Sources (Learnings, Autopsies, Ledger)
                
                # --- SOURCE A: Governance Learning Items ---
                query_learnings = "SELECT * FROM governance_learning_items WHERE project_id != ?"
                params_l = [self.current_project_id]
                
                # Filter by domain if provided
                if domain:
                    query_learnings += " AND target_domain = ?"
                    params_l.append(domain)
                
                learnings_res = await session.execute(query_learnings, params_l)
                for l in learnings_res:
                    score = self._calculate_match_score(l, domain, problem_type, project_similarities)
                    if score > 0.3:
                        results.append(self._format_result(l, "LEARNING", score, project_similarities))

                # --- SOURCE B: Governance Autopsies ---
                # Search in root_cause or reason
                query_autopsies = "SELECT * FROM governance_autopsies WHERE project_id != ?"
                params_a = [self.current_project_id]
                autopsies_res = await session.execute(query_autopsies, params_a)
                for a in autopsies_res:
                    # Score based on content matching and project similarity
                    score = self._calculate_content_match_score(a, "root_cause_analysis", problem_type, project_similarities)
                    if score > 0.3:
                        results.append(self._format_result(a, "AUTOPSY", score, project_similarities))

                # --- SOURCE C: Decision Ledger ---
                query_ledger = "SELECT * FROM governance_decision_ledger WHERE project_id != ?"
                params_led = [self.current_project_id]
                ledger_res = await session.execute(query_ledger, params_led)
                for led in ledger_res:
                    score = self._calculate_content_match_score(led, "rationale", problem_type, project_similarities)
                    if score > 0.3:
                        results.append(self._format_result(led, "DECISION", score, project_similarities))

                # 3. Final Ranking and Traceability
                results = sorted(results, key=lambda x: x["similarity_score"], reverse=True)
                
                # Save Trace
                search_id = f"SRCH_{uuid.uuid4().hex[:8]}"
                await session.execute("""
                    INSERT INTO governance_cross_project_search_traces (search_id, query_context, target_project_id, results_json)
                    VALUES (?, ?, ?, ?)
                """, (
                    search_id, 
                    json.dumps({"domain": domain, "type": problem_type, "keywords": rationale_keywords}),
                    self.current_project_id,
                    json.dumps(results[:10]) # Top 10 for trace
                ))
                
        return results

    def _calculate_match_score(self, obj, target_domain, target_type, project_similarities) -> float:
        score = 0.0
        p_similarity = project_similarities.get(obj["project_id"], 0.2) # Base similarity if unknown
        
        # Domain match (Strong signal)
        if target_domain and obj.get("target_domain") == target_domain:
            score += 0.5
        elif not target_domain:
            score += 0.2
            
        # Type match
        if target_type and target_type.lower() in (obj.get("learning_type") or "").lower():
            score += 0.3
            
        # Project similarity boost
        score += (p_similarity * 0.2)
        
        return min(1.0, score)

    def _calculate_content_match_score(self, obj, field, target_type, project_similarities) -> float:
        score = 0.0
        p_similarity = project_similarities.get(obj["project_id"], 0.2)
        
        content = (obj.get(field) or "").lower()
        if target_type and target_type.lower() in content:
            score += 0.6
        
        score += (p_similarity * 0.4)
        return min(1.0, score)

    def _format_result(self, obj, obj_type, score, project_similarities) -> Dict[str, Any]:
        band = "MATCH_FUERTE" if score > 0.7 else "MATCH_PARCIAL" if score > 0.4 else "REFERENCIA_CONTEXTUAL"
        
        # Human readable summary
        summary = ""
        if obj_type == "LEARNING": summary = f"Lección sobre {obj.get('target_domain')}: {obj.get('lesson_summary')}"
        elif obj_type == "AUTOPSY": summary = f"Causa raíz detectada: {obj.get('root_cause_analysis')[:100]}..."
        elif obj_type == "DECISION": summary = f"Decisión de tipo {obj.get('decision_type')}: {obj.get('rationale')[:100]}..."
        
        return {
            "source_project_id": obj.get("project_id"),
            "source_object_type": obj_type,
            "source_object_id": obj.get("learning_item_id") or obj.get("autopsy_id") or obj.get("ledger_id"),
            "similarity_score": round(score, 2),
            "relevance_band": band,
            "lesson_summary": summary,
            "transfer_risk": "Bajo" if score > 0.8 else "Moderado (Similitud parcial)" if score > 0.5 else "Alto (Referencia leve)",
            "rationale": f"Match de tipo {band} con un score de {score}. Proviene de un proyecto con similitud {project_similarities.get(obj.get('project_id'), 'n/a')}."
        }

cross_project_search_engine = CrossProjectSearchEngine()
