"""
Workspace bridge scaffold.

This layer should expose controlled actions from Creator chat to:
- active file inspection
- diff preview
- patch proposal
- chip inspection
- dashboard evidence collection
"""

from typing import Any, Dict


class WorkspaceBridge:
    def inspect_active_file(self) -> Dict[str, Any]:
        return {"status": "not_implemented", "action": "inspect_active_file"}

    def get_diff_preview(self) -> Dict[str, Any]:
        return {"status": "not_implemented", "action": "get_diff_preview"}

    def collect_runtime_evidence(self) -> Dict[str, Any]:
        return {"status": "not_implemented", "action": "collect_runtime_evidence"}
