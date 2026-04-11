import logging
from enum import Enum
from typing import List, Dict, Optional
from .ledger import forge_ledger

logger = logging.getLogger(__name__)

class RecommendationStrength(Enum):
    STRONG = "strong"
    WEAK = "weak"
    INSUFFICIENT = "insufficient"

class ForgeRecommender:
    """
    Forge Contextual Recommendation Layer (Block 80).
    Converts telemetry evidence into bounded strategic suggestions.
    """
    
    def __init__(self):
        self.min_samples_strong = 5
        self.min_samples_weak = 1

    async def get_recommendations(self, context_filter: Optional[str] = None, strategy_lens: str = "balanced") -> List[dict]:
        """
        Analyzes the ledger through a strategic lens (Block V2.2).
        """
        history = await forge_ledger.list_history(limit=500)
        
        # Group by Capability + Provider
        groups = {}
        for entry in history:
            cap = entry['capability_class']
            pid = entry['provider_id']
            key = (cap, pid)
            if key not in groups:
                groups[key] = []
            groups[key].append(entry)
            
        recommendations = []
        distinct_caps = set(k[0] for k in groups.keys())
        
        for cap in distinct_caps:
            cap_providers = {k[1]: v for k, v in groups.items() if k[0] == cap}
            
            rankings = []
            for pid, entries in cap_providers.items():
                stats = self._calculate_stats(entries)
                if stats['count'] >= self.min_samples_weak:
                    rankings.append({
                        "pid": pid,
                        "stats": stats,
                        "privacy": entries[0]['privacy_band'],
                        "is_sovereign": entries[0]['privacy_band'] == "sovereign_native" or "local" in pid
                    })
            
            if not rankings: continue
                
            # V2.2 Multi-Dimensional Sorting
            if strategy_lens == "performance":
                # Lower latency is better. 
                # Primary: latency, Secondary: quality
                rankings.sort(key=lambda x: (x['stats']['latency'], -x['stats']['quality']))
            elif strategy_lens == "privacy":
                # Sovereign first. Secondary: quality
                rankings.sort(key=lambda x: (x['is_sovereign'], x['stats']['quality']), reverse=True)
            elif strategy_lens == "reliability":
                # Success rate primary
                rankings.sort(key=lambda x: (x['stats']['success_rate'], x['stats']['quality']), reverse=True)
            else: # Balanced
                rankings.sort(key=lambda x: (x['stats']['quality'], x['stats']['success_rate']), reverse=True)
            
            top = rankings[0]
            strength = RecommendationStrength.STRONG if top['stats']['count'] >= self.min_samples_strong else RecommendationStrength.WEAK
            
            tradeoff = f"Optimal baseline for {strategy_lens} lens."
            if len(rankings) > 1:
                runner_up = rankings[1]
                if strategy_lens == "performance":
                    tradeoff = f"Fastest verified provider (+{int(runner_up['stats']['latency'] - top['stats']['latency'])}ms gain over {runner_up['pid']})."
                elif strategy_lens == "privacy" and top['is_sovereign'] and not runner_up['is_sovereign']:
                    tradeoff = f"Maintains local data sovereignty (Runner-up {runner_up['pid']} is remote)."
                elif top['stats']['quality'] > runner_up['stats']['quality']:
                    tradeoff = f"Superior quality than {runner_up['pid']} but check latency ({int(top['stats']['latency'])}ms)."
            
            recommendations.append({
                "capability": cap,
                "suggested_provider": top['pid'],
                "strength": strength.value,
                "rationale": f"[{strategy_lens.upper()}] Reliability {top['stats']['success_rate']*100:.0f}% | Quality {top['stats']['quality']:.2f}.",
                "tradeoff": tradeoff,
                "context_tag": context_filter or "general_performance",
                "sample_count": top['stats']['count'],
                "is_sovereign": top['is_sovereign'],
                "lens": strategy_lens
            })
            
        return recommendations

    def _calculate_stats(self, entries: List[dict]) -> dict:
        total = len(entries)
        successes = sum(1 for e in entries if str(e['outcome_status']).lower() == 'success')
        avg_quality = sum(e['quality_score'] or 0.0 for e in entries) / total
        avg_latency = sum(e['latency_ms'] or 0 for e in entries) / total
        
        return {
            "count": total,
            "success_rate": successes / total,
            "quality": avg_quality,
            "latency": avg_latency
        }

# Global singleton
forge_recommender = ForgeRecommender()

# Global singleton
forge_recommender = ForgeRecommender()
