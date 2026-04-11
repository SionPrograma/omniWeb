from typing import Optional, Any
from .intent_detector import LanguageIntentDetector
from .response_composer import ResponseComposer

class LanguageOrchestrator:
    """
    Main Sovereign Orchestrator for the Language Domain.
    Ties together Intent Detection, Composition, Policy, and external Tooling gracefully.
    """
    def __init__(self):
        self.detector = LanguageIntentDetector()
        self.composer = ResponseComposer()
        
    def orchestrate(self, msg: str, ctx: Any, lang: str) -> Optional[str]:
        # 1. Detect Intent
        msg_clean = msg.lower().strip()
        intent_info = self.detector.detect_intent(msg_clean)
        
        # 2. Add Contextual Hints
        if ctx:
            intent_info["context"] = ctx
        intent_info["lang"] = lang
        
        # 3. Compose Response (Fallback or Tooling -> Policy)
        response = self.composer.compose(intent_info)
        
        return response
