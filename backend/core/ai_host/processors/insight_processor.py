import logging
from typing import Dict, Any, Optional, List
from .base import CommandProcessor, AICommandResponse
from backend.core.insight_engine.engine import insight_engine

logger = logging.getLogger(__name__)

class InsightProcessor(CommandProcessor):
    """
    AI Host Processor for Actionable Insights.
    Phase 19: Actionable Insight Engine.
    """

    async def can_handle(self, command: str) -> bool:
        terms = ["analiza mis ideas", "analyze my ideas", "system insights", "insights del sistema", "patrones", "patterns", "sugerencias", "suggestions"]
        cmd = command.lower()
        return any(term in cmd for term in terms)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        user_id = str(context.get("user_id", "1")) if context else "1"
        
        # Trigger fresh analysis
        insights = await insight_engine.analyze_user(user_id)
        
        if not insights:
            return AICommandResponse(
                intent="insight_analysis",
                status="success",
                message="He analizado tu sistema y memoria, pero no he detectado patrones o anomalías importantes por ahora. ¡Todo parece estar en orden!"
            )
            
        # Format insights for user
        text = "### 💡 Insights y Sugerencias Detectadas\n"
        for i in insights:
            icon = "🔴" if i.severity == "critical" else "🟠" if i.severity == "warning" else "🔵"
            text += f"\n{icon} **{i.title}**\n   {i.description}\n"
            
        text += "\n¿Te gustaría que convierta alguna de estas sugerencias en una tarea oficial?"

        return AICommandResponse(
            intent="insight_analysis",
            status="success",
            message=text,
            payload={"insight_count": len(insights)}
        )
