"""
Evaluation ledger scaffold.

Records how a model/tool/agent performed for future routing and improvement.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class EvaluationEntry:
    mission_id: str
    provider: str
    model_name: str
    capability_type: str
    success: bool
    tests_passed: bool
    creator_approved: bool
    notes: str = ""


class EvaluationLedger:
    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    def record(self, entry: EvaluationEntry) -> None:
        self.entries.append(asdict(entry))
