import logging
import os
import uuid
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AuditIssue(BaseModel):
    id: str = str(uuid.uuid4())
    title: str
    layer: str
    severity: str # critical, warning, info
    cause: str
    affected_files: List[str] = []
    suggested_action: str

class CorrectionProposal(BaseModel):
    issue_id: str
    title: str
    probable_fix: str
    files_to_modify: List[str]
    expected_effect: str
    risk_level: str # low, medium, high

class SystemAuditor:
    """
    Component responsible for scanning the system and identifying issues.
    """
    def __init__(self):
        self.last_audit_results: List[AuditIssue] = []

    async def audit_system(self) -> List[AuditIssue]:
        """Runs a full system audit."""
        logger.info("[AUDITOR] Auditing system...")
        issues = []
        
        # 1. Check for basic system stability (Mocked for Phase 2)
        # In a real scenario, this would check logs, database connectivity, memory, etc.
        from backend.core.config import settings
        if not settings.IS_ADMIN_TOKEN_SAFE:
            issues.append(AuditIssue(
                title="Insecure Admin Token",
                layer="Security",
                severity="critical",
                cause="The system is using the default OMNIWEB_ADMIN_TOKEN.",
                affected_files=["backend/core/config.py"],
                suggested_action="Configure a unique OMNIWEB_ADMIN_TOKEN in the environment."
            ))

        # 2. Check for missing chips or corrupt registry
        # (Scenario for tests)
        if not os.path.exists("chips/chip-reparto"):
            issues.append(AuditIssue(
                title="Missing Core Chip: Reparto",
                layer="Logistics",
                severity="warning",
                cause="The 'Reparto' chip directory is missing from the filesystem.",
                affected_files=["chips/chip-reparto/"],
                suggested_action="Initialize the Reparto chip using the Project Initializer."
            ))

        self.last_audit_results = issues
        return issues

    async def audit_chip(self, chip_slug: str) -> List[AuditIssue]:
        """Audits a specific chip."""
        logger.info(f"[AUDITOR] Auditing chip: {chip_slug}...")
        issues = []
        
        # Mock logic for "Reparto" chip
        if chip_slug == "reparto":
             issues.append(AuditIssue(
                title="Reparto: Optimization Buffer Empty",
                layer="Execution",
                severity="warning",
                cause="The logistics optimizer has no active workload buffer.",
                affected_files=[f"chips/chip-{chip_slug}/core/optimizer.py"],
                suggested_action="Increase the default workload throughput in the optimizer config."
            ))
        
        return issues

    async def generate_proposal(self, issue: AuditIssue) -> CorrectionProposal:
        """Generates a structured correction proposal for an issue."""
        return CorrectionProposal(
            issue_id=issue.id,
            title=f"Fix: {issue.title}",
            probable_fix=issue.suggested_action,
            files_to_modify=issue.affected_files,
            expected_effect="System stability restored and risk mitigated.",
            risk_level="low" if issue.severity != "critical" else "medium"
        )

system_auditor = SystemAuditor()
