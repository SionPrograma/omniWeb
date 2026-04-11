import logging
from typing import Optional, Any
from ..engine.orchestrator import LanguageOrchestrator

logger = logging.getLogger(__name__)

class LanguageEngine:
    """
    Open-Source Native Language Chip.
    Refactored to Sovereign Orchestration Architecture.
    Delegates all processing to the LanguageOrchestrator, maintaining backward
    compatibility with the existing `brain_router` hook.
    """
    
    def __init__(self):
        self.orchestrator = LanguageOrchestrator()
    
    async def enhance_natural_chat(self, msg: str, ctx: Any, lang: str) -> Optional[str]:
        # Route to official sovereign architecture
        return self.orchestrator.orchestrate(msg, ctx, lang)

language_engine = LanguageEngine()
