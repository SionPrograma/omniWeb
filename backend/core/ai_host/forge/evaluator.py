import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from .ledger import forge_ledger

logger = logging.getLogger(__name__)

class ForgeMemoryEvaluator:
    """
    Block 83: Strategic Replay Evaluator.
    Compares performance benchmarks before and after a strategic swap.
    """
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size

    async def evaluate_swap_outcome(self, request_id: int) -> Dict:
        """
        Analyzes whether a specific swap improved system performance.
        """
        # 1. Fetch Swap Details
        all_reqs = await forge_ledger.list_requests()
        req = next((r for r in all_reqs if r['id'] == request_id), None)
        
        if not req or req['status'] != 'APPLIED' or not req['applied_at']:
            return {"verdict": "INVALID_OR_NOT_APPLIED", "reason": "Request not found or not in applied state."}

        applied_at = req['applied_at']
        capability = req['capability']
        from_provider = req['from_provider']
        to_provider = req['to_provider']

        # 2. Extract Windows
        # Note: We query the ledger for the specific capability and providers
        # 'Before' window uses from_provider before applied_at
        # 'After' window uses to_provider after applied_at
        
        history = await forge_ledger.list_history(limit=500) # Get a slice
        
        before_samples = [h for h in history if h['capability_class'] == capability 
                          and from_provider in h['provider_id']
                          and h['timestamp'] < applied_at][:self.window_size]
                          
        after_samples = [h for h in history if h['capability_class'] == capability 
                         and to_provider in h['provider_id']
                         and h['timestamp'] >= applied_at][:self.window_size]

        if len(before_samples) < 5 or len(after_samples) < 5:
            return {
                "verdict": "INSUFFICIENT_DATA",
                "reason": f"Need at least 5 samples per window. Found {len(before_samples)} before, {len(after_samples)} after.",
                "stats": {"before_n": len(before_samples), "after_n": len(after_samples)}
            }

        # 3. Calculate Deltas
        def _avg(samples, key):
            vals = [s[key] for s in samples if s[key] is not None]
            return sum(vals) / len(vals) if vals else 0

        before_lat = _avg(before_samples, 'latency_ms')
        after_lat = _avg(after_samples, 'latency_ms')
        before_qual = _avg(before_samples, 'quality_score')
        after_qual = _avg(after_samples, 'quality_score')
        
        lat_delta = (after_lat - before_lat) / before_lat if before_lat > 0 else 0
        qual_delta = (after_qual - before_qual) if before_qual > 0 else after_qual
        
        # 4. Classify Verdict
        verdict = "MIXED"
        if lat_delta < -0.1 and qual_delta >= -0.05:
            verdict = "IMPROVED" # Significant latency drop
        elif qual_delta > 0.1:
            verdict = "IMPROVED" # Significant quality gain
        elif lat_delta > 0.2 and qual_delta <= 0:
            verdict = "DEGRADED" # Significant latency spike
        elif qual_delta < -0.1:
            verdict = "DEGRADED" # Quality drop
            
        return {
            "verdict": verdict,
            "capability": capability,
            "transition": f"{from_provider} -> {to_provider}",
            "stats": {
                "before": {"lat_ms": round(before_lat, 1), "qual": round(before_qual, 2), "n": len(before_samples)},
                "after": {"lat_ms": round(after_lat, 1), "qual": round(after_qual, 2), "n": len(after_samples)},
                "deltas": {"lat_pct": round(lat_delta * 100, 1), "qual": round(qual_delta, 2)}
            },
            "reasoning": f"Replay identified {verdict} status based on {len(after_samples)} post-swap events."
        }

# Global singleton
forge_evaluator = ForgeMemoryEvaluator()
