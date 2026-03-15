from typing import Dict, Any, Optional
import logging
from .base import CommandProcessor, AICommandResponse
from backend.core.permissions import enforce_permission, GOVERNANCE_ADVISOR_ACCESS

logger = logging.getLogger(__name__)

class GovernanceAdvisorProcessor(CommandProcessor):
    """
    GOVERNANCE ADVISOR
    Phase 4: AI Governance Advisor.
    Recommends governance actions to the Creator/Admin.
    """

    async def can_handle(self, command: str) -> bool:
        keywords = ["recomienda", "governance", "advisor", "consejo", "users", "administrar", "insights de gobierno"]
        return any(k in command.lower() for k in keywords)

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        # Enforce permission (Only Creator/Admin)
        try:
            enforce_permission(GOVERNANCE_ADVISOR_ACCESS)
        except Exception:
            return AICommandResponse(
                intent="governance_denied",
                status="denied",
                message="Only the Creator or authorized Administrators can access Governance Advice."
            )

        from backend.core.governance.manager import governance_manager
        insights = governance_manager.get_pending_insights()
        
        # Also run leadership detection on demand
        from backend.core.governance.leadership_engine import leadership_engine
        await leadership_engine.analyze_users()
        
        insights = governance_manager.get_pending_insights() # Refresh
        
        if not insights:
            return AICommandResponse(
                intent="governance_advisor",
                status="success",
                message="The community is stable. No urgent governance actions detected. All testers are behaving within expected parameters."
            )

        # Summarize insights
        summary = "### 🏛️ Governance Advisor Recommendations\n\n"
        for insight in insights:
            summary += f"- **{insight.insight_type.upper()}**: {insight.message}\n"

        summary += "\n\n*You can approve these promotions in Mission Control → Governance Panel.*"

        return AICommandResponse(
            intent="governance_advisor",
            status="success",
            message=summary,
            payload={"insights": [i.model_dump() for i in insights]}
        )

governance_advisor_processor = GovernanceAdvisorProcessor()
