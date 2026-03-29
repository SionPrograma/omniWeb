
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AIToolDefinition(BaseModel):
    name: str
    description: str
    category: str # operational, diagnostic, chat, context, memory
    required_mode: Optional[str] = None # natural_chat, action_execution, etc.

class ToolRegistry:
    """
    Registry of ordered tools available to the AI Host.
    Encapsulates tool metadata for better selection logic.
    """
    def __init__(self):
        self._tools: Dict[str, AIToolDefinition] = {}
        self._initialize_core_tools()

    def _initialize_core_tools(self):
        core_tools = [
            AIToolDefinition(name="chat", description="General conversational response", category="chat", required_mode="natural_chat"),
            AIToolDefinition(name="communication", description="Fallback communication layer", category="chat"),
            AIToolDefinition(name="diagnostic", description="Deep system analysis and health check", category="diagnostic", required_mode="operational_diagnostic"),
            AIToolDefinition(name="proposal", description="Code and architecture proposals (fixes)", category="operational", required_mode="constrained_output"),
            AIToolDefinition(name="memory", description="Semantic and historical retrieval", category="memory"),
            AIToolDefinition(name="chip_action", description="Direct interaction with system chips", category="operational", required_mode="action_execution"),
            AIToolDefinition(name="supercommand", description="Long-running complex orchestration", category="operational", required_mode="swarm_orchestration"),
            AIToolDefinition(name="logbook", description="Audit technical execution history", category="diagnostic"),
        ]
        for t in core_tools:
            self.register(t)

    def register(self, tool: AIToolDefinition):
        self._tools[tool.name] = tool

    def get_candidates(self, mode: str, intent: str) -> List[str]:
        """
        Returns a list of tools that are compatible with the current mode and intent.
        """
        candidates = []
        for name, tool in self._tools.items():
            # If no mode required or matches current mode
            if not tool.required_mode or tool.required_mode == mode:
                candidates.append(name)
        
        # If still empty or very limited, add basic chat fallback
        if "chat" not in candidates: candidates.append("chat")
        return list(set(candidates)) # Unique only

tool_registry = ToolRegistry()
