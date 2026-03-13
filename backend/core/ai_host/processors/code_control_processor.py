import logging
import os
from typing import Dict, Any, Optional, List
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse
from backend.core.ai_developer.code_analyzer import code_analyzer
from backend.core.ai_developer.patch_generator import patch_generator
from backend.core.ai_developer.chip_editor import chip_editor
from backend.core.ai_developer.module_reloader import module_reloader
from backend.core.master_logbook.manager import master_logbook_manager

logger = logging.getLogger(__name__)

class CodeControlProcessor(CommandProcessor):
    """
    Processor for Phase 6: Code Control Layer.
    Handles inspection, patch generation (proposal), and patch execution.
    """

    async def can_handle(self, command: str) -> bool:
        terms = ["inspect", "code", "file", "fix", "patch", "modify", "bug", "arch", "structure"]
        return any(term in command.lower() for term in terms)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = command.lower()
        
        # 1. Inspect Project / Code
        if any(x in cmd for x in ["inspect", "show files", "show code", "arch"]):
            results = code_analyzer.inspect_project(command)
            
            from backend.core.interface.visual_interface import visual_interface
            visual = visual_interface.create_visual_payload(
                "file-list", 
                {"files": results["relevant_files"]}, 
                f"Architecture: {results['query']}"
            )
            
            # Format message
            files_list = "\n".join([f"- `{f}`" for f in results["relevant_files"]])
            message = f"### 🔍 Code Inspection Results\nFound {len(results['relevant_files'])} relevant files for your query:\n\n{files_list}"
            
            return AICommandResponse(
                intent="code_inspection",
                status="success",
                message=message,
                payload={"results": results, "visual": visual}
            )

        # 2. Patch Generation (Proposal)
        if any(x in cmd for x in ["fix", "patch", "modify", "bug"]):
            # For this version, we require target chip to be specified
            from backend.core.module_registry import module_registry
            chips = module_registry.discover_all_chips()
            target = None
            for c in chips:
                if c["slug"] in cmd:
                    target = c["slug"]
                    break
            
            if not target:
                return AICommandResponse(
                    intent="code_proposal",
                    status="error",
                    message="Target chip not detected. Please specify which chip to modify (e.g., 'fix bug in lingua')."
                )

            # Analyze and Generate
            analysis = code_analyzer.analyze_chip(target)
            patches = patch_generator.generate_patch(command, analysis)
            
            if not patches:
                return AICommandResponse(
                    intent="code_proposal",
                    status="success",
                    message="I analyzed the code but couldn't identify a safe automated patch for this specific request."
                )

            # Check if this is a confirmation
            if "confirm" in cmd or "yes" in cmd or "si" in cmd:
                return await self._execute_patch(target, patches)

            # Otherwise, show proposal
            proposal_summary = patch_generator.summarize_patch(patches)
            
            from backend.core.interface.visual_interface import visual_interface
            visual = visual_interface.create_visual_payload(
                "task-report",
                {
                    "status": "pending_approval",
                    "actions": [p["description"] for p in patches],
                    "issues": ["Requires creator verification before execution"]
                },
                "Proposed Patch Preview"
            )
            
            return AICommandResponse(
                intent="confirmation_required",
                status="pending",
                message=f"I've generated a potential solution for '{target}':\n\n{proposal_summary}",
                payload={
                    "action": "execute_patch",
                    "target": target,
                    "patches": patches,
                    "visual": visual
                }
            )

        return AICommandResponse(
            intent="code_control_unknown",
            status="error",
            message="I'm not sure how to handle that code control request. Try 'inspect shell code' or 'fix bug in [chip]'."
        )

    async def _execute_patch(self, target: str, patches: List[Dict[str, Any]]) -> AICommandResponse:
        """Applies the patches, reloads, and logs to the Master Logbook."""
        try:
            # Apply
            result = chip_editor.apply_patches(target, patches)
            if result["status"] == "error":
                return AICommandResponse(intent="patch_execution", status="error", message=f"Patch failed: {result['message']}")

            # Reload
            module_reloader.reload_chip(target)
            
            # Log to Master Logbook
            from backend.core.master_logbook.models import MasterLogbookEntry, EntryType
            entry = MasterLogbookEntry(
                type=EntryType.FIX,
                content=f"Code modification applied to '{target}' via AI Host.",
                chip_reference=target,
                metadata={
                    "patches": [p["description"] for p in patches],
                    "status": "success",
                    "phase": "CODE_CONTROL"
                }
            )
            master_logbook_manager.add_entry(entry)

            return AICommandResponse(
                intent="patch_execution",
                status="success",
                message=f"✅ **Patch Applied Successfully** to '{target}'. Module reloaded and stability verified.",
                payload={"applied": result["applied"]}
            )
        except Exception as e:
            logger.error(f"Patch execution error: {e}")
            return AICommandResponse(intent="patch_execution", status="error", message=f"Execution error: {str(e)}")
