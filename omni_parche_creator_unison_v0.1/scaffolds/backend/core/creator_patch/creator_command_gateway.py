"""
Additive scaffold for Creator Command Gateway.

Purpose:
Normalize raw Creator chat input into structured command objects
without replacing the current chat system.

Expected integration zone:
- existing ai host / brain router / creator copilot chat endpoint

This is a scaffold, not a final patch.
Antigravity should adapt it to the real runtime and real imports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CreatorCommand:
    raw_input: str
    intent: str = "unknown"
    execution_mode: str = "analyze"
    target_scope: Optional[str] = None
    needs_tools: bool = False
    needs_models: bool = False
    needs_approval: bool = False
    context_sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CreatorCommandGateway:
    """
    Wrap current Creator chat input and emit normalized command objects.
    """

    def normalize(self, raw_input: str, context: Optional[Dict[str, Any]] = None) -> CreatorCommand:
        context = context or {}
        return CreatorCommand(
            raw_input=raw_input,
            intent=context.get("intent", "unknown"),
            execution_mode=context.get("execution_mode", "analyze"),
            target_scope=context.get("target_scope"),
            needs_tools=context.get("needs_tools", False),
            needs_models=context.get("needs_models", False),
            needs_approval=context.get("needs_approval", False),
            context_sources=context.get("context_sources", []),
            metadata=context,
        )
