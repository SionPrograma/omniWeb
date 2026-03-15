import os
import json
import logging
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.core.system_auditor.models import SystemAuditReport, AuditIssue, AutoFixProposal, FixAction, AuditStatus
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
        self._fix_history: Dict[str, int] = {}
        self._loop_threshold = 3

    @property
    def is_active(self) -> bool:
        return self._is_applying or any(p.status == "applying" for p in self.active_proposals.values())

    async def analyze_report(self, report: SystemAuditReport) -> List[AutoFixProposal]:
        """
        Identifies fixable issues in a report and generates proposals.
        """
        proposals = []
        for issue in report.issues:
            try:
                # Use string comparison to avoid Enum instance mismatch issues
                level_str = str(issue.level).split(".")[-1]
                if level_str in ["WARNING", "ERROR"]:
                    issue_key = f"{issue.sector}:{issue.message}".lower().strip()
                    if self._fix_history.get(issue_key, 0) >= self._loop_threshold:
                        logger.warning(f"AutoFixEngine: Skipping repeated issue (Loop Detection): {issue_key}")
                        continue
                    
                    proposal = await self._generate_fix(issue)
                    if proposal:
                        proposals.append(proposal)
                        self.active_proposals[proposal.id] = proposal
                        self._fix_history[issue_key] = self._fix_history.get(issue_key, 0) + 1
            except Exception as e:
                logger.error(f"Error in AutoFixEngine loop: {e}")
        
        return proposals

    async def _generate_fix(self, issue: AuditIssue) -> Optional[AutoFixProposal]:
        """
        Root Cause Analysis & Fix Generation.
        """
        msg = issue.message.lower()
        fp = (issue.fingerprint or "").lower()
        
        # 1. Fix missing chip.json fields
        if "manifest missing required fields" in msg or "has no entry point defined" in msg:
            return self._fix_manifest_missing_fields(issue)
            
        # 2. Fix missing chip entry point
        if "entry point missing on disk" in msg:
            return self._fix_missing_entry_point(issue)

        # 3. Fix simple AI pipeline cleanup
        if "ai pipeline cleanup delay" in msg:
            return self._fix_temp_file_leak(issue)
            
        # 4. Fix missing router file (stabilization phase)
        if "missing_router_file" in fp:
            return self._fix_missing_router_file(issue)

        # 5. Fix unloaded backend (code error/transient)
        if "unloaded_backend" in fp:
            return self._fix_unloaded_backend(issue)

        # 6. Fix registration failed (missing from registry)
        if "registration_failed" in fp:
            return self._fix_registration_failed(issue)

        return None

    def _fix_manifest_missing_fields(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            chip_folder = issue.message.split("Chip ")[1].split(" ")[0]
            patch_content = {}
            if "manifest missing required fields" in issue.message:
                fields_part = issue.message.split(": ")[1]
                missing_fields = [f.strip() for f in fields_part.split(",")]
                for field in missing_fields:
                    if field == "version": patch_content["version"] = "0.1.0"
                    if field == "name": patch_content["name"] = chip_folder.replace("chip-", "").capitalize()
                    if field == "slug": patch_content["slug"] = chip_folder.replace("chip-", "")
                    if field == "id": patch_content["id"] = chip_folder
            
            if "has no entry point defined" in issue.message:
                patch_content["entry_frontend"] = "index.html"
                patch_content["has_frontend"] = True

            actions = [FixAction(
                type="file_patch",
                target=os.path.join("chips", chip_folder, "chip.json"),
                description=f"Update manifest to restore consistency for {chip_folder}",
                patch_data={"action": "replace_json_fields", "content": patch_content}
            )]
            return AutoFixProposal(issue_message=issue.message, analysis=f"Manifest fix for {chip_folder}", actions=actions)
        except: return None

    def _fix_missing_entry_point(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            parts = issue.message.split("Chip ")[1].split(" entry point")
            chip_folder = parts[0]
            entry_file = parts[1].split(": ")[1].strip()
            actions = [FixAction(
                type="file_create",
                target=os.path.join("chips", chip_folder, entry_file),
                description=f"Create skeleton entry point '{entry_file}'",
                patch_data={"content": f"<!DOCTYPE html><html><body><h1>{chip_folder}</h1></body></html>"}
            )]
            return AutoFixProposal(issue_message=issue.message, analysis=f"Entry point recovery for {chip_folder}", actions=actions)
        except: return None

    def _fix_temp_file_leak(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            path = issue.message.split("in ")[1]
            return AutoFixProposal(issue_message=issue.message, analysis="Temp disk cleanup", actions=[FixAction(type="cleanup", target=path, description=f"Cleanup {path}")])
        except: return None

    def _fix_missing_router_file(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            # Handle both 'missing_router_file:slug' and 'missing_router_file:chip-slug'
            raw_target = issue.fingerprint.split(":")[1]
            chip_folder = raw_target if raw_target.startswith("chip-") else f"chip-{raw_target}"
            
            target = os.path.join("chips", chip_folder, "core", "router.py")
            content = "from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/status')\nasync def s(): return {'status': 'active'}\n"
            actions = [FixAction(type="file_create", target=target, description=f"Create router.py for {chip_folder}", patch_data={"content": content})]
            return AutoFixProposal(issue_message=issue.message, analysis=f"Missing router for {chip_folder}", actions=actions)
        except: return None

    def _fix_unloaded_backend(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            slug = issue.fingerprint.split(":")[1]
            actions = [FixAction(type="module_reload", target=slug, description=f"Reload chip {slug}")]
            return AutoFixProposal(issue_message=issue.message, analysis=f"Attempting to recovery crashed backend for {slug}", actions=actions)
        except: return None

    def _fix_registration_failed(self, issue: AuditIssue) -> AutoFixProposal:
        try:
            slug = issue.fingerprint.split(":")[1]
            # When registration fails completely, we attempt a full system re-init or targeted chip re-init
            actions = [FixAction(type="module_reload", target=slug, description=f"Re-attempting registration for {slug}")]
            return AutoFixProposal(issue_message=issue.message, analysis=f"Chip {slug} is missing from runtime registry. Triggering re-registration.", actions=actions)
        except: return None

    async def apply_fix(self, proposal_id: str) -> bool:
        """
        Executes the actions in an approved proposal.
        """
        proposal = self.active_proposals.get(proposal_id)
        if not proposal: return False
            
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
                                    os.remove(os.path.join(action.target, f))
                                success_count += 1
                        
                        elif action.type == "module_reload":
                            slug = action.target
                            # Use module_reloader for chips, or ai_host if specified
                            if slug != "ai_host":
                                module_reloader.reload_chip(slug)
                            success_count += 1
                    except Exception as e:
                        logger.error(f"Action failed in fix {proposal.id}: {e}")

                is_done = success_count == len(proposal.actions)
                proposal.status = "applied" if is_done else "failed"
                self._is_applying = False
                
                await self._log_fix_to_master(proposal)
                return is_done
        except Exception as e:
            self._is_applying = False
            logger.error(f"Error applying fix {proposal_id}: {e}")
            return False

    async def _log_fix_to_master(self, proposal: AutoFixProposal):
        try:
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
                metadata={"proposal_id": proposal.id, "status": proposal.status}
            )
            master_logbook_manager.add_entry(entry)
        except: pass

fix_engine = AutoFixEngine()
