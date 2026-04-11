import logging
from typing import Optional, List, Dict, Any
from ..forge.drift import forge_drift_advisor
from ..forge.aggregator import forge_debt_aggregator
from ..intent_understanding.conversation_tracker import conversation_tracker, SessionContext

logger = logging.getLogger(__name__)

class StrategicNarrativeBridge:
    """
    Bridges the gap between Forge strategic signals and Conversational output.
    Allows Omni to mention Drift, Debt, and Replays in natural dialogue.
    """
    
    async def get_advisory_fragment(self, session_id: str) -> Optional[str]:
        """
        Scans Forge for relevant, high-severity news to share with the Creator.
        """
        ctx = conversation_tracker.get_context(session_id)
        
        # 1. Fetch Candidates (Prioritize HIGH severity)
        drifts = await forge_drift_advisor.getting_drift_advisories()
        debts = await forge_debt_aggregator.get_debt_clusters()
        
        advisory = None
        advisory_id = None
        
        # 2. SELECT MOST RELEVANT SIGNAL
        # Logic: 
        # - High Severity Drift wins if it matches active entities
        # - High Severity Debt wins if provider matches active providers
        # - Fallback to highest severity global signal
        
        # High Drift Search
        for d in drifts:
            if d['severity'] == "HIGH":
                aid = f"drift_{d['capability']}_{d['recommended_provider']}"
                if self._is_suppressed(ctx, aid): continue
                
                if d['capability'] in ctx.active_entities or not advisory:
                    advisory = f"He notado una **Desviación Estratégica Crítica** en '{d['capability']}'. La Forge recomienda '{d['recommended_provider']}' para resolver {d['tradeoff']['priority']}. ¿Quieres revisar el Swap Request?"
                    advisory_id = aid
                    break

        # High Debt Search (if no drift found)
        if not advisory:
            for db in debts:
                if db['severity'] == "HIGH":
                    aid = f"debt_{db['capability']}_{db['provider']}"
                    if self._is_suppressed(ctx, aid): continue
                    
                    if db['capability'] in ctx.active_entities or db['provider'] in ctx.active_providers or not advisory:
                        advisory = f"Atención: Hay un cluster de **Deuda Técnica** en '{db['capability']}' ({db['provider']}). He registrado {db['occurrence_count']} fallas recurrentes. Sugiero una auditoría de remediación."
                        advisory_id = aid
                        break

        # 3. Suppress and Return
        if advisory and advisory_id:
            self._suppress(ctx, advisory_id)
            return advisory
            
        return None

    def _is_suppressed(self, ctx: SessionContext, advisory_id: str) -> bool:
        suppressions = ctx.metadata.get("narrative_suppressions", [])
        return advisory_id in suppressions

    def _suppress(self, ctx: SessionContext, advisory_id: str):
        if "narrative_suppressions" not in ctx.metadata:
            ctx.metadata["narrative_suppressions"] = []
        ctx.metadata["narrative_suppressions"].append(advisory_id)
        # Keep manageable list
        if len(ctx.metadata["narrative_suppressions"]) > 10:
            ctx.metadata["narrative_suppressions"].pop(0)

strategic_narrative_bridge = StrategicNarrativeBridge()
