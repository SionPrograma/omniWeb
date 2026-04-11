import logging
import asyncio
from typing import List, Dict, Optional
from .recommender import forge_recommender
from .ledger import forge_ledger
from .config_manager import forge_config_manager

logger = logging.getLogger(__name__)

class ForgeDriftAdvisor:
    """
    V2.4: Strategic Drift Advisor.
    Detects when active configurations deviate from Forge-validated best-fit context patterns.
    """
    
    def __init__(self):
        # Baseline defaults if no override exists
        self.baselines = {
            "transcription": "whisper-base",
            "translation": "remote-nmt",
            "synthesis": "edge-tts"
        }

    async def getting_drift_advisories(self, capability: Optional[str] = None) -> List[Dict]:
        """
        Analyzes alignment between current active config and Forge recommendations.
        """
        # 1. Get current best-fit (Balanced lens)
        recommendations = await forge_recommender.get_recommendations(strategy_lens="balanced")
        
        advisories = []
        for rec in recommendations:
            cap = rec['capability']
            if capability and cap != capability: continue
            
            # 2. Get active provider
            default = self.baselines.get(cap, "unknown")
            active = await forge_config_manager.get_provider(cap, default)
            
            # 3. Detect Drift
            # We ONLY flag drift if:
            # - The suggested provider is DIFFERENT from active
            # - The recommendation strength is STRONG
            if active != rec['suggested_provider'] and rec['strength'] == 'strong':
                severity = "MEDIUM"
                
                # Check if current active has a debt cluster (V2.3 synergy)
                from .aggregator import forge_debt_aggregator
                debt_clusters = await forge_debt_aggregator.get_debt_clusters(cap)
                active_debt = next((c for c in debt_clusters if c['provider'] == active), None)
                
                reason = f"Active configuration ({active}) is misaligned with validated best-fit ({rec['suggested_provider']})."
                if active_debt:
                    severity = "HIGH"
                    reason += f" Current provider '{active}' has an associated Structural Debt cluster."

                advisories.append({
                    "capability": cap,
                    "active_provider": active,
                    "recommended_provider": rec['suggested_provider'],
                    "severity": severity,
                    "reason": reason,
                    "evidence_strength": rec['strength'].upper(),
                    "tradeoff": rec['tradeoff'],
                    "timestamp": rec.get('last_updated', "CURRENT")
                })

        return advisories

# Global singleton
forge_drift_advisor = ForgeDriftAdvisor()
