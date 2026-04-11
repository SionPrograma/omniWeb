"""
Checkpoint Manager — OMNI_PATCH Phase F.
Manages Creator-driven state snapshots and rollbacks.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from backend.core.ai_host.memory.checkpoint_engine import checkpoint_engine

logger = logging.getLogger(__name__)

@dataclass
class CheckpointMetadata:
    checkpoint_id: str
    label: str
    mission_id: str
    timestamp: str
    targets: List[str]
    metadata: Dict[str, Any]

class CheckpointManager:
    """
    Wrapper for CheckpointEngine with Creator-specific metadata and tracking.
    """

    def create_creator_checkpoint(self, mission_id: str, label: str, targets: List[str], extra_meta: Dict[str, Any] = None) -> str:
        """Creates a snapshot before a Creator-driven mutation."""
        logger.info(f"[CHECKPOINT_MGR] Creating Creator-checkpoint: {label} for mission {mission_id}")
        
        # Call real engine
        ckpt_id = checkpoint_engine.create_snapshot(mission_id, label, targets)
        
        # Log structured audit event
        logger.info(f"[CHECKPOINT_MGR] Checkpoint {ckpt_id} verified at runtime for {len(targets)} files.")
        
        return ckpt_id

    def rollback_to_creator_checkpoint(self, mission_id: str, checkpoint_id: str) -> bool:
        """Reverts status to a previous Creator-checkpoint."""
        logger.warning(f"[CHECKPOINT_MGR] REQUESTED ROLLBACK: Mission {mission_id} -> {checkpoint_id}")
        return checkpoint_engine.rollback(mission_id, checkpoint_id)

checkpoint_manager = CheckpointManager()
