import os
import json
import logging
from typing import List, Optional, Dict, Any
from .models import SystemAuditReport, AuditIssue, AutoFixProposal, FixAction, AuditStatus
from backend.core.logger import logger
from backend.core.ai_developer.chip_editor import chip_editor
from backend.core.ai_developer.module_reloader import module_reloader
from backend.core.permissions import set_chip_context

class AutoFixEngine:
    """
    OmniWeb Self-Healing System.
    Analyzes audit reports and applies corrective patches.
    """
    
    def __init__(self):
        self.active_proposals: Dict[str, AutoFixProposal] = {}
        self._is_applying = False
        self._fix_history: Dict[str, int] = {} # issue_hash: count
        self._loop_threshold = 3 # max attempts per session for same issue

    @property
    def is_active(self) -> bool:
        return self._is_applying or any(p.status == "applying" for p in self.active_proposals.values())

    async def analyze_report(self, report: SystemAuditReport) -> List[AutoFixProposal]:
        """
        Identifies fixable issues in a report and generates proposals.
        """
        proposals = []
        for issue in report.issues:
            if issue.level in [AuditStatus.WARNING, AuditStatus.ERROR]:
                issue_key = issue.message.lower().strip()
                if self._fix_history.get(issue_key, 0) >= self._loop_threshold:
                    logger.warning(f"AutoFixEngine: Skipping repeated issue (Loop Detection): {issue_key}")
                    continue
                
                proposal = await self._generate_fix(issue)
                if proposal:
                    proposals.append(proposal)
                    self.active_proposals[proposal.id] = proposal
                    self._fix_history[issue_key] = self._fix_history.get(issue_key, 0) + 1
        
        return proposals

    async def _generate_fix(self, issue: AuditIssue) -> Optional[AutoFixProposal]:
        """
        Root Cause Analysis & Fix Generation.
        """
        msg = issue.message.lower()
        
        # 1. Fix missing chip.json fields
        if "manifest missing required fields" in msg or "has no entry point defined" in msg:
            return self._fix_manifest_missing_fields(issue)
            
        # 2. Fix missing chip entry point
        if "entry point missing on disk" in msg:
            return self._fix_missing_entry_point(issue)

        # 3. Fix simple AI pipeline cleanup
        if "ai pipeline cleanup delay" in msg or "ai pipeline cleanup leak" in msg:
            return self._fix_temp_file_leak(issue)
            
        # 4. Fix unregistered AI Processor
        if "crucial ai processor missing" in msg:
             return self._fix_processor_registration(issue)

        return None

    def _fix_manifest_missing_fields(self, issue: AuditIssue) -> AutoFixProposal:
        # Expected: "Chip chip-slug manifest missing required fields: name, slug"
        try:
            chip_folder = issue.message.split("Chip ")[1].split(" manifest")[0] if "manifest" in issue.message else issue.message.split("Chip ")[1].split(" has")[0]
            
            actions = []
            patch_content = {}
            
            if "manifest missing required fields" in issue.message:
                fields_part = issue.message.split(": ")[1]
                missing_fields = [f.strip() for f in fields_part.split(",")]
                for field in missing_fields:
                    if field == "version": patch_content["version"] = "0.1.0"
                    if field == "description": patch_content["description"] = "Auto-generated description"
                    if field == "type": patch_content["type"] = "hybrid"
                    if (field == "entry" or field == "entry_frontend"): patch_content[field] = "index.html"
                    if field == "name": patch_content["name"] = chip_folder.replace("chip-", "").capitalize()
                    if field == "slug": patch_content["slug"] = chip_folder.replace("chip-", "")
                    if field == "id": patch_content["id"] = chip_folder
            
            if "has no entry point defined" in issue.message:
                patch_content["entry_frontend"] = "index.html"
                patch_content["has_frontend"] = True

            actions.append(FixAction(
                type="file_patch",
                target=os.path.join("chips", chip_folder, "chip.json"),
                description=f"Update manifest to restore consistency",
                patch_data={
                    "action": "replace_json_fields",
                    "content": patch_content
                }
            ))

            return AutoFixProposal(
                issue_message=issue.message,
                analysis=f"The manifest for {chip_folder} is incomplete. Adding defaults to restore functionality.",
                actions=actions
            )
        except Exception as e:
            logger.error(f"Failed to parse manifest issue for fix: {e}")
            return None

    def _fix_missing_entry_point(self, issue: AuditIssue) -> AutoFixProposal:
        # e.g. "Chip chip-music entry point missing on disk: index.html"
        try:
            parts = issue.message.split("Chip ")[1].split(" entry point")
            chip_folder = parts[0]
            entry_file = parts[1].split(": ")[1]
            
            actions = []
            if entry_file.strip().endswith(".html"):
                actions.append(FixAction(
                    type="file_create",
                    target=os.path.join("chips", chip_folder, entry_file.strip()),
                    description=f"Create default entry point '{entry_file.strip()}'",
                    patch_data={
                        "content": f"<!DOCTYPE html>\n<html>\n<head><title>{chip_folder}</title></head>\n<body>\n<h1>{chip_folder}</h1>\n<p>OmniWeb Auto-Generated Entry Point</p>\n</body>\n</html>"
                    }
                ))

            return AutoFixProposal(
                issue_message=issue.message,
                analysis=f"Chip {chip_folder} cannot launch because its entry point {entry_file} is missing. Creating a placeholder.",
                actions=actions
            )
        except Exception as e:
            logger.error(f"Failed to parse entry point issue for fix: {e}")
            return None

    def _fix_temp_file_leak(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            path = issue.message.split("in ")[1]
            actions = [FixAction(
                type="cleanup",
                target=path,
                description=f"Clear temporary files in {path}"
            )]
            return AutoFixProposal(
                issue_message=issue.message,
                analysis="Excessive temporary files detected in AI pipeline workspace. Triggering automated cleanup.",
                actions=actions
            )
        except: return None

    def _fix_processor_registration(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            processor_name = issue.message.split(": ")[1]
            actions = [FixAction(
                type="module_reload",
                target="ai_host",
                description=f"Reload AI Host to attempt registration of {processor_name}"
            )]
            return AutoFixProposal(
                issue_message=issue.message,
                analysis=f"The processor '{processor_name}' is not active. A module reload may re-initialize the registry.",
                actions=actions
            )
        except: return None

    async def apply_fix(self, proposal_id: str) -> bool:
        """
        Executes the actions in an approved proposal.
        """
        proposal = self.active_proposals.get(proposal_id)
        if not proposal:
            return False
            
        logger.info(f"Applying fix: {proposal.id} - {proposal.issue_message}")
        proposal.status = "applying"
        self._is_applying = True
        
        try:
            with set_chip_context("core"):
                success_count = 0
                for action in proposal.actions:
                    try:
                        if action.type == "file_patch":
                            path = action.target
                            if path.endswith(".json"):
                                with open(path, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                data.update(action.patch_data["content"])
                                with open(path, "w", encoding="utf-8") as f:
                                    json.dump(data, f, indent=4)
                                success_count += 1
                        
                        elif action.type == "file_create":
                            os.makedirs(os.path.dirname(action.target), exist_ok=True)
                            with open(action.target, "w", encoding="utf-8") as f:
                                f.write(action.patch_data["content"])
                            success_count += 1
                            
                        elif action.type == "cleanup":
                            if os.path.exists(action.target):
                                for f in os.listdir(action.target):
                                    f_path = os.path.join(action.target, f)
                                    if os.path.isfile(f_path):
                                        os.remove(f_path)
                                success_count += 1
                        
                        elif action.type == "module_reload":
                            slug = action.target
                            if slug != "ai_host":
                                module_reloader.reload_chip(slug)
                            success_count += 1
                    except Exception as e:
                        logger.error(f"Action failed in fix {proposal.id}: {e}")

                is_done = success_count == len(proposal.actions)
                proposal.status = "applied" if is_done else "failed"
                self._is_applying = False
                
                # Log to master logbook
                await self._log_fix_to_master(proposal)
                
                return is_done
        except Exception as e:
            self._is_applying = False
            logger.error(f"Error applying fix {proposal_id}: {e}")
            return False

    async def _log_fix_to_master(self, proposal: AutoFixProposal):
        from backend.core.master_logbook.manager import master_logbook_manager
        from backend.core.master_logbook.models import MasterLogbookEntry, EntryType, Priority, EntryStatus
        
        content = f"### 🏗️ Auto Fix Executed: {proposal.id}\n\n"
        content += f"**Issue:** {proposal.issue_message}\n"
        content += f"**Analysis:** {proposal.analysis}\n"
        content += f"**Status:** {proposal.status.upper()}\n\n"
        content += "#### Actions Taken:\n"
        for a in proposal.actions:
            content += f"- [{a.type}] {a.description} (Target: {a.target})\n"
            
        entry = MasterLogbookEntry(
            type=EntryType.AUTO_FIX,
            content=content,
            priority=Priority.HIGH,
            status=EntryStatus.DONE if proposal.status == "applied" else EntryStatus.OPEN,
            metadata={
                "proposal_id": proposal.id,
                "status": proposal.status,
                "affected_files": [a.target for a in proposal.actions]
            }
        )
        master_logbook_manager.add_entry(entry)

fix_engine = AutoFixEngine()
