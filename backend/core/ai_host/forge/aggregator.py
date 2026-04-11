import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .ledger import forge_ledger

logger = logging.getLogger(__name__)

class ForgeDebtAggregator:
    """
    V2.3: Auto-Autopsy Aggregation.
    Clusters recurring failure and degradation patterns into Structural Debt.
    """
    
    def __init__(self):
        self.failure_threshold = 3 # Min occurrences to form a cluster
        self.lookback_days = 7

    async def get_debt_clusters(self, capability: Optional[str] = None) -> List[Dict]:
        """
        Scans history to identify strategic weak points.
        """
        history = await forge_ledger.list_history(limit=1000)
        
        # 1. Cluster by (Capability, Provider, Context)
        clusters = {}
        for entry in history:
            # We focus on non-SUCCESS outcomes
            if entry['outcome_status'].lower() == 'success' and entry['quality_score'] >= 0.5:
                continue
                
            cap = entry['capability_class']
            if capability and cap != capability: continue
            
            p_id = entry['provider_id']
            ctx = "global" # Simplified context for V2.3 clustering
            key = (cap, p_id, ctx)
            
            if key not in clusters:
                clusters[key] = {
                    "capability": cap,
                    "provider_id": p_id,
                    "context": ctx,
                    "failures": 0,
                    "degradations": 0,
                    "fallbacks": 0,
                    "sample_count": 0,
                    "total_samples": 0, # To calculate rate
                    "latest_evidence": None
                }
            
            status = entry['outcome_status'].lower()
            if status in ['fail', 'error', 'timeout']:
                clusters[key]["failures"] += 1
            elif entry['quality_score'] < 0.5:
                clusters[key]["degradations"] += 1
            
            clusters[key]["sample_count"] += 1
            clusters[key]["latest_evidence"] = entry['timestamp']

        # 2. Filter and refine
        debt_results = []
        for key, data in clusters.items():
            if data['sample_count'] < self.failure_threshold: continue
            
            # Categorize Debt
            debt_type = "RELIABILITY_GAP"
            severity = "LOW"
            if data['failures'] > (data['sample_count'] * 0.5):
                debt_type = "CRITICAL_FAILURE_ZONE"
                severity = "HIGH"
            elif data['degradations'] > (data['sample_count'] * 0.5):
                debt_type = "QUALITY_DEGRADATION"
                severity = "MEDIUM"

            debt_results.append({
                "title": f"Systemic {debt_type.replace('_', ' ')}",
                "capability": data['capability'],
                "provider": data['provider_id'],
                "context": data['context'],
                "occurrence_count": data['sample_count'],
                "severity": severity,
                "debt_type": debt_type,
                "evidence_strength": "STRONG" if data['sample_count'] > 10 else "MODERATE",
                "reasoning": f"Detected {data['failures']} hard failures and {data['degradations']} degradations in recent samples."
            })

        return sorted(debt_results, key=lambda x: (x['severity'] == "HIGH", x['occurrence_count']), reverse=True)

# Global singleton
forge_debt_aggregator = ForgeDebtAggregator()
