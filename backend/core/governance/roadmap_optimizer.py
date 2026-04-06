import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from datetime import datetime

logger = logging.getLogger(__name__)

class RoadmapOptimizerEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE STRATEGIC ROADMAP OPTIMIZER.
    Prudently suggests a sequence for tactical interventions.
    """
    
    def __init__(self):
        self.priority_types = {
            "RELIEF_ACTION_PACKAGE": 0.9,
            "ROOT_AUDIT_ACTION_PACKAGE": 0.7,
            "SAFE_REFACTOR_PACKAGE": 0.6,
            "PREVENTIVE_STABILIZATION_PACKAGE": 0.8,
            "EXPERIMENTAL_GUARDED_PACKAGE": 0.4
        }

    def run_full_optimization(self):
        """
        Gathers all candidates and rebuilds the roadmap.
        """
        candidates = self._fetch_candidates()
        if not candidates:
            logger.info("No candidates for roadmap optimization.")
            return []

        # 1. Scouring & Enrichment
        scored_items = []
        for c in candidates:
            score = self._calculate_item_score(c)
            scored_items.append({**c, "calc_score": score})

        # 2. Sort by score
        scored_items.sort(key=lambda x: x["calc_score"], reverse=True)

        # 3. Handle Chain & Rank
        final_roadmap = []
        for rank, item in enumerate(scored_items):
            rank_obj = self._build_roadmap_item(item, rank + 1)
            final_roadmap.append(rank_obj)

        # 4. Save to DB
        self._persist_roadmap(final_roadmap)
        return final_roadmap

    def _fetch_candidates(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            packages = conn.execute("""
                SELECT package_id as source_id, 'ACTION_PACKAGE' as source_type, * 
                FROM governance_action_packages 
                WHERE creator_decision = 'PENDING'
            """).fetchall()
            return [dict(p) for p in packages]

    def _calculate_item_score(self, item: Dict[str, Any]) -> float:
        base = self.priority_types.get(item["package_type"], 0.5)
        conf = item.get("confidence", 0.5)
        
        # Urgency injection (Placeholder for future Pressure integration)
        urgency = 0.5
        if item["risk_level"] == "HIGH": 
             urgency += 0.2
             
        score = (base * 0.4) + (conf * 0.3) + (urgency * 0.3)
        return score

    def _build_roadmap_item(self, item: Dict[str, Any], rank: int) -> Dict[str, Any]:
        p_band = "HIGH_PRIORITY_NEXT"
        if item["calc_score"] > 0.85: p_band = "EXECUTE_NOW"
        if item["calc_score"] < 0.5: p_band = "DEFER_LOW_RETURN"
        
        # Rationale creation
        reason = f"Prioridad basada en {item['package_type']} con confianza de {item.get('confidence', 0):.2f}."
        if item["risk_level"] == "HIGH":
             reason += " El riesgo elevado exige atención prioritaria."

        return {
            "item_id": f"RMAP-{item['source_id']}",
            "source_type": item["source_type"],
            "source_id": item["source_id"],
            "suggested_rank": rank,
            "priority_band": p_band,
            "urgency_score": item.get("calc_score", 0.5),
            "expected_relief": 0.7 if item["package_type"].startswith("RELIEF") else 0.5,
            "expected_cost": 0.3,
            "dependency_refs": json.dumps([]),
            "rationale": reason,
            "recommended_timing": "Inmediato" if p_band == "EXECUTE_NOW" else "Próxima Ventana",
            "blockers": json.dumps([]),
            "confidence": item.get("confidence", 0.5)
        }

    def _persist_roadmap(self, roadmap: List[Dict[str, Any]]):
        with db_manager.get_connection() as conn:
            # We don't delete history, but we update or insert.
            # To keep it simple: we clear 'NONE' state entries before re-inserting full fresh roadmap.
            conn.execute("DELETE FROM governance_roadmap_optimizations WHERE creator_override_state = 'NONE'")
            
            for item in roadmap:
                conn.execute("""
                    INSERT INTO governance_roadmap_optimizations (
                        item_id, source_type, source_id, suggested_rank, priority_band,
                        urgency_score, expected_relief, expected_cost, dependency_refs,
                        rationale, recommended_timing, blockers, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item["item_id"], item["source_type"], item["source_id"], item["suggested_rank"],
                    item["priority_band"], item["urgency_score"], item["expected_relief"],
                    item["expected_cost"], item["dependency_refs"], item["rationale"],
                    item["recommended_timing"], item["blockers"], item["confidence"]
                ))
            conn.commit()

    def get_current_roadmap(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_roadmap_optimizations ORDER BY suggested_rank ASC").fetchall()
            return [dict(r) for r in rows]

    def update_item_override(self, item_id: str, state: str) -> bool:
        """state: FIXED, IGNORED, MOVED"""
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE governance_roadmap_optimizations 
                SET creator_override_state = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE item_id = ?
            """, (state, item_id))
            conn.commit()
            return True

roadmap_optimizer = RoadmapOptimizerEngine()
