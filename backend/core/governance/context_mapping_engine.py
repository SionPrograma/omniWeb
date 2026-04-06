import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class ContextMappingEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE MULTI-PROJECT CONTEXTUAL MAPPING.
    Detects tactical similarities between projects and suggests baselines.
    """
    
    def __init__(self):
        self.current_project_id = "PROJECT_OMNIWEB_PROD" # Default for now
        
    async def profile_current_context(self) -> Dict[str, Any]:
        """
        Generates a DNA fingerprint of the current project state.
        """
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                # 1. Domains from handoffs/missions
                res_domains = await session.execute("SELECT DISTINCT target_domain FROM governance_chat_signals WHERE target_domain IS NOT NULL")
                domains = [r["target_domain"] for r in res_domains]
                
                # 2. Risk Profile (Avg Friction from branches)
                res_risk = await session.execute("SELECT AVG(friction) as avg_f, COUNT(*) as cnt FROM roadmap_branches")
                risk_data = res_risk.fetchone()
                avg_friction = risk_data["avg_f"] or 0.0
                branch_count = risk_data["cnt"] or 0
                
                # 3. Learning Density
                res_learnings = await session.execute("SELECT COUNT(*) as cnt FROM governance_learning_items")
                learning_count = res_learnings.fetchone()["cnt"] or 0
                
                # 4. Active Thresholds
                res_params = await session.execute("SELECT param_key, current_value FROM governance_engine_parameters")
                thresholds = {r["param_key"]: r["current_value"] for r in res_params}
                
                profile = {
                    "project_id": self.current_project_id,
                    "primary_domains": domains,
                    "risk_profile": {
                        "avg_friction": avg_friction,
                        "branch_count": branch_count,
                        "learning_density": learning_count / (branch_count or 1)
                    },
                    "learning_count": learning_count,
                    "thresholds": thresholds
                }
                
                # Save context profile
                await session.execute("""
                    INSERT OR REPLACE INTO governance_project_contexts (
                        context_id, project_id, primary_domains, risk_profile_dna, 
                        learning_density, active_thresholds, confidence, rationale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"CTX_{self.current_project_id}", self.current_project_id,
                    json.dumps(domains), json.dumps(profile["risk_profile"]),
                    profile["risk_profile"]["learning_density"], json.dumps(thresholds),
                    1.0, "Auto-profiling of current production environment."
                ))
                
                return profile

    async def scan_contextual_matches(self, target_project_id: str) -> List[Dict[str, Any]]:
        """
        Compares target project with existing profiles to find matches.
        """
        matches = []
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                # Get target (usually current) profile
                t_res = await session.execute("SELECT * FROM governance_project_contexts WHERE project_id = ?", (target_project_id,))
                target = t_res.fetchone()
                if not target: return []
                
                t_domains = set(target["primary_domains"] if isinstance(target["primary_domains"], list) else json.loads(target["primary_domains"] or "[]"))
                
                # Fetch all other profiles
                sources_res = await session.execute("SELECT * FROM governance_project_contexts WHERE project_id != ?", (target_project_id,))
                
                for source in sources_res:
                    s_domains = set(source["primary_domains"] if isinstance(source["primary_domains"], list) else json.loads(source["primary_domains"] or "[]"))
                    
                    # 1. Similarity Logic: Jaccard on domains + friction similarity
                    shared = t_domains.intersection(s_domains)
                    domain_similarity = len(shared) / len(t_domains.union(s_domains)) if t_domains.union(s_domains) else 0.0
                    
                    # 2. Risk DNA similarity
                    s_dna = json.loads(source["risk_profile_dna"] or "{}")
                    t_dna = json.loads(target["risk_profile_dna"] or "{}")
                    
                    friction_diff = abs(s_dna.get("avg_friction", 0) - t_dna.get("avg_friction", 0))
                    risk_match = max(0, 1 - (friction_diff / 50)) # Linear decay up to 50% diff
                    
                    total_score = (domain_similarity * 0.7) + (risk_match * 0.3)
                    
                    if total_score > 0.4:
                        # Identify match type
                        if total_score > 0.8: match_type = "STRONG_CONTEXT_MATCH"
                        elif total_score > 0.6: match_type = "SOFT_CONTEXT_MATCH"
                        else: match_type = "REUSABLE_LEARNING_ONLY"
                        
                        # Identify transferable baselines
                        s_thresholds = json.loads(source["active_thresholds"] or "{}")
                        t_thresholds = json.loads(target["active_thresholds"] or "{}")
                        
                        suggested_params = {}
                        for k, v in s_thresholds.items():
                            if k in t_thresholds and abs(v - t_thresholds[k]) > 0.01:
                                suggested_params[k] = v
                                
                        # Find relevant learnings
                        # (In real scenario, would filter governance_learning_items by domains)
                        
                        mapping_id = f"MAP_{source['project_id']}_{target_project_id}"
                        
                        mapping_data = {
                            "mapping_id": mapping_id,
                            "source_project_id": source["project_id"],
                            "target_project_id": target_project_id,
                            "similarity_score": total_score,
                            "match_type": match_type,
                            "shared_domains": list(shared),
                            "suggested_baseline_params": suggested_params,
                            "rationale": f"Similitud detectada en dominios ({len(shared)}) y perfil de fricción histórica.",
                            "transfer_risk": "Bajo" if total_score > 0.7 else "Moderado (Similitud parcial)"
                        }
                        
                        # Save mapping
                        await session.execute("""
                            INSERT OR REPLACE INTO governance_contextual_mappings (
                                mapping_id, source_project_id, target_project_id,
                                similarity_score, match_type, shared_domains,
                                suggested_baseline_params, rationale, transfer_risk,
                                status, creator_action_required
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            mapping_id, source["project_id"], target_project_id,
                            total_score, match_type, json.dumps(list(shared)),
                            json.dumps(suggested_params), mapping_data["rationale"], mapping_data["transfer_risk"],
                            "PROPOSED", 1
                        ))
                        matches.append(mapping_data)

        return matches

    async def execute_transfer(self, mapping_id: str, keys_to_accept: List[str] = None):
        """
        Applies selected baselines from the mapping to the current project.
        """
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                res = await session.execute("SELECT * FROM governance_contextual_mappings WHERE mapping_id = ?", (mapping_id,))
                mapping = res.fetchone()
                if not mapping: raise ValueError("Mapping not found")
                
                params = json.loads(mapping["suggested_baseline_params"] or "{}")
                for key, val in params.items():
                    if keys_to_accept is None or key in keys_to_accept:
                        # Update engine parameters
                        await session.execute(
                            "UPDATE governance_engine_parameters SET current_value = ?, last_recalibrated_at = CURRENT_TIMESTAMP WHERE param_key = ?",
                            (val, key)
                        )
                
                await session.execute(
                    "UPDATE governance_contextual_mappings SET status = ?, applied_at = CURRENT_TIMESTAMP, creator_action_required = 0 WHERE mapping_id = ?",
                    ("ACCEPTED" if not keys_to_accept else "PARTIAL", mapping_id)
                )

context_mapping_engine = ContextMappingEngine()
