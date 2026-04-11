"""
Capability router scaffold.

Responsibilities:
- decide whether a mission needs tools/models
- choose capability class
- enforce local-first or policy constraints
"""

from typing import Any, Dict


class CapabilityRouter:
    def route(self, command: Dict[str, Any]) -> Dict[str, Any]:
        intent = command.get("intent", "unknown")

        if intent in {"audit", "review", "compare"}:
            return {"capability_type": "review", "needs_approval": False}

        if intent in {"patch", "edit", "refactor"}:
            return {"capability_type": "code", "needs_approval": True}

        if intent in {"summarize", "document"}:
            return {"capability_type": "documentation", "needs_approval": False}

        return {"capability_type": "general", "needs_approval": False}
