import logging
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
from .ledger import forge_ledger
from .evaluator import forge_evaluator
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class ForgeAffinityManager:
    """
    V2.0: Context Affinity Memory.
    Summarizes long-term performance patterns of providers across contexts.
    """
    
    async def get_affinities(self, capability: Optional[str] = None) -> List[Dict]:
        """Retrieves stored context affinities."""
        def _fetch():
            with db_manager.get_connection(internal=True) as conn:
                query = "SELECT * FROM intelligence_forge_affinity_memory"
                params = []
                if capability:
                    query += " WHERE capability = ?"
                    params.append(capability)
                query += " ORDER BY affinity_score DESC"
                rows = conn.execute(query, params).fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_fetch)

    async def derive_affinity_from_replay(self, request_id: int):
        """
        Updates affinity memory based on a Strategic Replay autopsy.
        A positive (IMPROVED) autopsy significantly strengthens context affinity.
        """
        outcome = await forge_evaluator.evaluate_swap_outcome(request_id)
        verdict = outcome.get("verdict")
        if verdict == "INSUFFICIENT_DATA": return

        capability = outcome.get("capability")
        context = outcome.get("transition") # Transition is our 'context' for now
        provider = outcome.get("transition").split(" -> ")[1] # The 'After' provider
        verdict = outcome.get("verdict")
        
        # 1. Map verdict to score delta
        score_delta = 0.0
        trend = "STABLE"
        if verdict == "IMPROVED": 
            score_delta = 0.2
            trend = "IMPROVING"
        elif verdict == "DEGRADED": 
            score_delta = -0.3
            trend = "DEGRADING"
        elif verdict == "MIXED": 
            score_delta = -0.05
            trend = "MIXED"

        # 2. Persist
        def _upsert():
            with db_manager.get_connection(internal=True) as conn:
                # Get current
                row = conn.execute("""
                    SELECT affinity_score, sample_count FROM intelligence_forge_affinity_memory
                    WHERE capability = ? AND context_tag = ? AND provider_id = ?
                """, (capability, context, provider)).fetchone()
                
                new_score = score_delta
                new_count = 1
                if row:
                    new_score = max(-1.0, min(1.0, row['affinity_score'] + score_delta))
                    new_count = row['sample_count'] + 1
                
                conn.execute("""
                    INSERT OR REPLACE INTO intelligence_forge_affinity_memory 
                    (capability, context_tag, provider_id, affinity_score, sample_count, outcome_trend, evidence_summary, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (capability, context, provider, new_score, new_count, trend, json.dumps(outcome.get("stats"))))
                conn.commit()
        
        await asyncio.to_thread(_upsert)
        logger.info(f"Forge Affinity Memory updated for {capability}:{context} -> {provider}")

# Global singleton
forge_affinity_manager = ForgeAffinityManager()
