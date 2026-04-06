import json
import logging
import uuid
import collections
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class WisdomMultiContextHarvester:
    """
    OMNIWEB — BLOQUE: GOVERNANCE MULTI-CONTEXT SYNC HARVESTER.
    Cosecha confirmaciones de sabiduría entre proyectos para proponer elevación
    a Strong Baselines o Candidate Global Policies.
    """
    
    def __init__(self):
        self.levels = {
            "LOCAL_PATTERN_ONLY": {"min_conf": 1, "min_proj": 1},
            "CROSS_CONTEXT_CONFIRMED_TACTIC": {"min_conf": 3, "min_proj": 2},
            "STRONG_REUSABLE_BASELINE": {"min_conf": 5, "min_proj": 3},
            "CANDIDATE_GLOBAL_POLICY": {"min_conf": 10, "min_proj": 4}
        }

    def scan_harvests(self) -> List[Dict[str, Any]]:
        """
        Agrupa syncs por nodo de sabiduría y calcula fuerza acumulada.
        """
        proposals = []
        with db_manager.get_connection() as conn:
            # Aggregate from syncs (which now includes project_id)
            syncs = conn.execute("""
                SELECT source_atlas_node_ids, actual_outcome_type, project_id
                FROM governance_post_mission_syncs
                WHERE creator_decision = 'ACCEPTED' AND is_applied = 1
            """).fetchall()
            
            node_stats = collections.defaultdict(lambda: {"conf": 0, "neg": 0, "projects": set()})
            
            for s in syncs:
                node_ids = json.loads(s["source_atlas_node_ids"])
                outcome = s["actual_outcome_type"]
                proj_id = s["project_id"]
                
                for nid in node_ids:
                    node_stats[nid]["projects"].add(proj_id)
                    if outcome == "WISDOM_CONFIRMED":
                        node_stats[nid]["conf"] += 1
                    elif outcome == "WISDOM_CONTRADICTED":
                        node_stats[nid]["neg"] += 1
                        
            for nid, stat in node_stats.items():
                proposal = self._evaluate_promotion(nid, stat)
                if proposal:
                    proposals.append(proposal)
                    
        self._persist_harvests(proposals)
        return proposals

    def _evaluate_promotion(self, node_id: str, stat: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        proj_count = len(stat["projects"])
        conf_count = stat["conf"]
        neg_count = stat["neg"]
        
        # Determine best level
        best_level = "LOCAL_PATTERN_ONLY"
        for level, reqs in self.levels.items():
            if conf_count >= reqs["min_conf"] and proj_count >= reqs["min_proj"]:
                best_level = level
                
        # Risk factor: more contradictions = more risk
        risk = 0.0
        if (conf_count + neg_count) > 0:
            risk = neg_count / (conf_count + neg_count)
            
        # Diversity score: Simple ratio of unique projects per confirmations
        diversity = proj_count / conf_count if conf_count > 0 else 0.0
        
        # Don't propose if it's already a harvest or if evidence is low
        if conf_count < 2: return None

        return {
            "harvest_id": f"HARV-{uuid.uuid4().hex[:8].upper()}",
            "atlas_node_id": node_id,
            "proposed_level": best_level,
            "confirmation_count": conf_count,
            "contradiction_count": neg_count,
            "project_count": proj_count,
            "context_diversity_score": diversity,
            "rationale": f"Cosecha basada en {conf_count} confirmaciones reales en {proj_count} proyectos distintos.",
            "transfer_risk": risk
        }

    def _persist_harvests(self, proposals: List[Dict[str, Any]]):
        with db_manager.get_connection() as conn:
            for p in proposals:
                # Evitar duplicados para el mismo nodo si ya hay una pendiente
                exists = conn.execute("SELECT 1 FROM governance_wisdom_harvests WHERE atlas_node_id = ? AND creator_decision = 'PENDING'", (p["atlas_node_id"],)).fetchone()
                if exists: continue
                
                conn.execute("""
                    INSERT INTO governance_wisdom_harvests (
                        harvest_id, atlas_node_id, proposed_level, confirmation_count, contradiction_count,
                        project_count, context_diversity_score, rationale, transfer_risk
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["harvest_id"], p["atlas_node_id"], p["proposed_level"], p["confirmation_count"], p["contradiction_count"],
                    p["project_count"], p["context_diversity_score"], p["rationale"], p["transfer_risk"]
                ))
            conn.commit()

    def get_pending_harvests(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("""
                SELECT h.*, n.title as node_title 
                FROM governance_wisdom_harvests h
                JOIN governance_wisdom_atlas_nodes n ON h.atlas_node_id = n.node_id
                WHERE h.creator_decision = 'PENDING'
            """).fetchall()
            return [dict(r) for r in rows]

    def apply_promotion(self, harvest_id: str) -> bool:
        with db_manager.get_connection() as conn:
            h = conn.execute("SELECT * FROM governance_wisdom_harvests WHERE harvest_id = ?", (harvest_id,)).fetchone()
            if not h or h["is_applied"]: return False
            
            # Update Node status band based on promotion
            # (In a real system, this might add global policies, here we update the band)
            conn.execute("""
                UPDATE governance_wisdom_atlas_nodes 
                SET status_band = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE node_id = ?
            """, (h["proposed_level"], h["atlas_node_id"]))
            
            conn.execute("UPDATE governance_wisdom_harvests SET creator_decision = 'ACCEPTED', is_applied = 1 WHERE harvest_id = ?", (harvest_id,))
            conn.commit()
            return True

wisdom_harvester = WisdomMultiContextHarvester()
