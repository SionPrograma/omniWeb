from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
from .ledger import forge_ledger
from .recommender import forge_recommender
from .evaluator import forge_evaluator
from .affinity import forge_affinity_manager
from .sync import forge_cross_sync
from .aggregator import forge_debt_aggregator
from .drift import forge_drift_advisor
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/forge", tags=["Intelligence Forge"])

class SwapRequestCreate(BaseModel):
    capability: str
    from_provider: str
    to_provider: str
    context: Optional[str] = None
    rationale: Optional[str] = None
    strength: Optional[str] = None
    tradeoff: Optional[str] = None

@router.get("/recommendations")
async def get_forge_recommendations(context: Optional[str] = None, lens: str = "balanced"):
    """
    Retrieves context-aware strategic suggestions from the Forge.
    """
    try:
        recommendations = await forge_recommender.get_recommendations(context_filter=context, strategy_lens=lens)
        return {
            "status": "ready",
            "recommendations": recommendations,
            "lens": lens,
            "interpretation": f"Advisory optimized for {lens}."
        }
    except Exception as e:
        logger.error(f"Forge Recommendation API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests")
async def list_swap_requests(status: Optional[str] = None):
    """Lists all strategic swap requests."""
    return {"status": "success", "requests": await forge_ledger.list_requests(status)}

@router.get("/requests/{id}/replay")
async def get_swap_replay(id: int):
    """Evaluates the outcome of a past strategic swap and updates affinity memory."""
    try:
        outcome = await forge_evaluator.evaluate_swap_outcome(id)
        # Block V2.0: Trigger Affinity Memory update on every autopsy
        await forge_affinity_manager.derive_affinity_from_replay(id)
        return {"status": "success", "outcome": outcome}
    except Exception as e:
        logger.error(f"Forge Replay API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/affinities")
async def list_forge_affinities(capability: Optional[str] = None):
    """Retrieves long-term context affinity memory."""
    affinities = await forge_affinity_manager.get_affinities(capability)
    return {"status": "success", "affinities": affinities}

@router.get("/synergies")
async def list_forge_synergies(chip: str = "lingua"):
    """
    Scans for and retrieves cross-domain strategic synergies.
    """
    await forge_cross_sync.scan_for_synergies()
    synergies = await forge_cross_sync.get_synergies(chip)
    return {"status": "success", "synergies": synergies}

@router.get("/structural-debt")
async def get_structural_debt_clusters(capability: Optional[str] = None):
    """
    Retrieves aggregated structural debt clusters (recurring failure patterns).
    """
    clusters = await forge_debt_aggregator.get_debt_clusters(capability)
    return {"status": "success", "clusters": clusters}

@router.get("/drift")
async def get_strategic_drift(capability: Optional[str] = None):
    """
    Analyzes alignment between active config and Forge recommendations.
    """
    advisories = await forge_drift_advisor.getting_drift_advisories(capability)
    return {"status": "success", "advisories": advisories}

@router.post("/requests/create")
async def create_swap_request(req: SwapRequestCreate):
    """Stages a new strategic swap request for Creator review."""
    request_id = await forge_ledger.create_swap_request(req.model_dump())
    return {"status": "staged", "request_id": request_id}

@router.post("/requests/{id}/apply")
async def apply_swap_request(id: int):
    """Approves and applies a strategic swap request."""
    success = await forge_ledger.apply_swap(id)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "applied"}

@router.get("/comparison")
async def get_comparison_summary():
    """
    Retrieves a condensed summary of provider performance for the Creator HUD.
    """
    try:
        history = await forge_ledger.list_history(limit=500)
        
        # Aggregate stats in memory (Block 79 aggregation)
        summary = {}
        
        for entry in history:
            cap = entry['capability_class']
            pid = entry['provider_id']
            
            if cap not in summary:
                summary[cap] = {}
            
            if pid not in summary[cap]:
                summary[cap][pid] = {
                    "provider_id": pid,
                    "count": 0,
                    "avg_latency": 0,
                    "avg_quality": 0,
                    "outcomes": {"success": 0, "partial": 0, "fail": 0, "timeout": 0},
                    "privacy_band": entry['privacy_band'],
                    "last_seen": entry['timestamp']
                }
            
            p_stats = summary[cap][pid]
            p_stats["count"] += 1
            # Running average
            p_stats["avg_latency"] = (p_stats["avg_latency"] * (p_stats["count"] - 1) + entry['latency_ms']) / p_stats["count"]
            p_stats["avg_quality"] = (p_stats["avg_quality"] * (p_stats["count"] - 1) + (entry['quality_score'] or 0.0)) / p_stats["count"]
            
            status = entry['outcome_status'].lower()
            if status in p_stats["outcomes"]:
                p_stats["outcomes"][status] += 1
                
        return {
            "status": "active",
            "capabilities": summary,
            "sample_size": len(history)
        }
    except Exception as e:
        logger.error(f"Forge API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_raw_history(limit: int = 50):
    """Full audit log for the Creator."""
    return await forge_ledger.list_history(limit=limit)
