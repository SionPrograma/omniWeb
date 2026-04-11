"""
Workspace Bridge — OMNI_PATCH Phase E.
Provides a higher-level interface for Creator Mode to interact with the workspace.
"""

import logging
import os
from typing import Any, Dict, Optional
from backend.core.creator_fs.file_system_router import validate_path
import difflib

logger = logging.getLogger(__name__)

class WorkspaceBridge:
    """
    Orchestration layer for workspace inspection and diffing.
    """

    async def inspect_active_file(self, path: str) -> Dict[str, Any]:
        """Reads and returns the content of a file within the workspace."""
        try:
            target_path = validate_path(path)
            if not os.path.exists(target_path):
                return {"status": "error", "message": f"File not found: {path}"}
            
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            logger.info(f"[WORKSPACE_BRIDGE] Inspected file: {path}")
            return {
                "status": "success",
                "path": path,
                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                "full_size": len(content)
            }
        except Exception as e:
            logger.error(f"[WORKSPACE_BRIDGE] Failed to inspect file {path}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_diff_preview(self, path: str, new_content: str) -> Dict[str, Any]:
        """Generates a unified diff for a proposed change."""
        try:
            target_path = validate_path(path)
            original_content = ""
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    original_content = f.read()
            
            diff = "".join(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile='original',
                tofile='proposed'
            ))
            
            logger.info(f"[WORKSPACE_BRIDGE] Generated diff for: {path}")
            return {
                "status": "success",
                "path": path,
                "diff": diff
            }
        except Exception as e:
            logger.error(f"[WORKSPACE_BRIDGE] Failed to generate diff for {path}: {e}")
            return {"status": "error", "message": str(e)}

    async def collect_runtime_evidence(self) -> Dict[str, Any]:
        """Calls the evidence engine to gather current system status."""
        try:
            from backend.core.ai_host.reasoning.evidence_engine import evidence_engine
            bundle = await evidence_engine.collect_evidence()
            
            logger.info(f"[WORKSPACE_BRIDGE] Collected runtime evidence: {len(bundle.items)} items")
            return {
                "status": "success",
                "evidence_summary": bundle.summary,
                "items_count": len(bundle.items),
                "snapshot_id": bundle.snapshot_id
            }
        except Exception as e:
            logger.error(f"[WORKSPACE_BRIDGE] Failed to collect evidence: {e}")
            return {"status": "error", "message": str(e)}

workspace_bridge = WorkspaceBridge()
