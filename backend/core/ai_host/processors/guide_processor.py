from typing import Dict, Any, Optional
import logging
from .base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class GuideProcessor(CommandProcessor):
    """
    UNIVERSAL SYSTEM GUIDE
    Phase 5: Self-Explaining Platform.
    Explains platform mechanics to users.
    """

    MECHANICS = {
        "admin": "To become an Admin, you must first progress through the Beta Tester role. Your behavior is analyzed for leadership signals, quality feedback, and community assistance. If detected, I will recommend you to the Creator for the Admin Candidate role.",
        "knowledge_graph": "The Knowledge Graph is your personal semantic memory. It connects your notes, logs, and explored concepts into a web of relationships, allowing you to see patterns in your own learning and work.",
        "opportunity_engine": "The Opportunity Engine analyzes your skills and the needs of the ecosystem to suggest collaborations, projects, or educational paths that maximize your potential.",
        "reputation": "Your reputation is a trust score built through positive interactions with other users and the system. It influences your eligibility for higher governance roles.",
        "chips": "Chips are modular applications within OmniWeb. Each chip adds specific functionality, like finance management, language translation, or code control."
    }

    async def can_handle(self, command: str) -> bool:
        keywords = ["what is", "how do i", "explain", "que es", "como", "feature", "mecanica"]
        return any(k in command.lower() for k in keywords)

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        msg_lower = msg.lower()
        
        response_text = "I am the OmniWeb AI Host, your universal guide. "
        
        if "admin" in msg_lower:
            response_text += self.MECHANICS["admin"]
        elif "knowledge graph" in msg_lower or "grafo" in msg_lower:
            response_text += self.MECHANICS["knowledge_graph"]
        elif "opportunity" in msg_lower or "oportunidad" in msg_lower:
            response_text += self.MECHANICS["opportunity_engine"]
        elif "reputation" in msg_lower or "reputacion" in msg_lower:
            response_text += self.MECHANICS["reputation"]
        elif "chip" in msg_lower:
            response_text += self.MECHANICS["chips"]
        else:
            response_text += "OmniWeb is a decentralized ecosystem for human development. You can ask me about any feature, role, or chip, and I will explain how it works."

        return AICommandResponse(
            intent="system_guide",
            status="success",
            message=response_text,
            payload={"guide": True}
        )

guide_processor = GuideProcessor()
