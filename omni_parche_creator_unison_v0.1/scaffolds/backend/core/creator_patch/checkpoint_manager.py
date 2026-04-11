"""
Checkpoint manager scaffold.

Creator-sensitive mutations should always have checkpoint metadata available.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Checkpoint:
    checkpoint_id: str
    label: str
    metadata: Dict[str, Any]


class CheckpointManager:
    def create_checkpoint(self, label: str, metadata: Dict[str, Any]) -> Checkpoint:
        return Checkpoint(checkpoint_id=f"ckpt:{label}", label=label, metadata=metadata)
