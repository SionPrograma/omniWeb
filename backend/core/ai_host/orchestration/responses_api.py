from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class InternalStructuredOutput(BaseModel):
    """
    Structured internal output for OmniWeb Chatbot Core.
    Used for ordered reasoning and clarity without exposing to final user.
    """
    intent: str
    confidence: float = 0.0
    required_memory: List[str] = []
    memory_sources_used: List[str] = []
    candidate_tools: List[str] = []
    selected_tool: Optional[str] = None
    response_mode: str = "direct_response"
    reasoning_trace: List[str] = []
    policy_constraints: Dict[str, Any] = {}
    final_status: str = "success"

class ResponsesAPI:
    """
    Modern API Core for conversational responses.
    Centralizes synthesis and internal structuring.
    """
    @staticmethod
    def create_internal_structure(
        intent: str,
        confidence: float,
        required_memory: List[str],
        candidate_tools: List[str],
        response_mode: str,
        selected_tool: Optional[str] = None,
        memory_sources_used: List[str] = None,
        reasoning_trace: List[str] = None,
        policy_constraints: Dict[str, Any] = None,
        final_status: str = "success"
    ) -> InternalStructuredOutput:
        return InternalStructuredOutput(
            intent=intent,
            confidence=confidence,
            required_memory=required_memory,
            memory_sources_used=memory_sources_used or [],
            candidate_tools=candidate_tools,
            selected_tool=selected_tool,
            response_mode=response_mode,
            reasoning_trace=reasoning_trace or [],
            policy_constraints=policy_constraints or {},
            final_status=final_status
        )
