import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import SystemAuditReport, AuditStatus, AuditSector, AuditIssue, AutoFixProposal
from .fix_engine import fix_engine
from backend.core.logger import logger
from backend.core.permissions import set_chip_context

class SystemAuditor:
    """
    OmniWeb System Self-Auditor Engine.
    Continuously evaluates the health of the OmniWeb environment.
    """
    
    def __init__(self):
        self.probes = []
        
    async def run_full_audit(self) -> SystemAuditReport:
        """
        Executes all registered probes and generates a comprehensive report.
        Ensures execution within 'core' context to allow system-level access.
        """
        logger.info("--- Starting Full System Audit ---")
        
        with set_chip_context("core"):
            issues: List[AuditIssue] = []
            metrics: Dict[str, Any] = {}
            
            # 1. Backend Probe
            backend_issues, backend_metrics = await self._audit_backend()
            issues.extend(backend_issues)
            metrics.update(backend_metrics)
            
            # 2. Chips Probe
            chip_issues, chip_metrics = await self._audit_chips()
            issues.extend(chip_issues)
            metrics.update(chip_metrics)
            
            # 3. PWA Probe
            pwa_issues, pwa_metrics = await self._audit_pwa()
            issues.extend(pwa_issues)
            metrics.update(pwa_metrics)
            
            # 4. Performance Probe
            perf_issues, perf_metrics = await self._audit_performance()
            issues.extend(perf_issues)
            metrics.update(perf_metrics)
            
            # 5. Frontend Probe
            fe_issues, fe_metrics = await self._audit_frontend()
            issues.extend(fe_issues)
            metrics.update(fe_metrics)
            
            # Determine overall status
            error_count = len([i for i in issues if i.level == AuditStatus.ERROR])
            warning_count = len([i for i in issues if i.level == AuditStatus.WARNING])
            
            if error_count > 0:
                overall_status = AuditStatus.ERROR
            elif warning_count > 0:
                overall_status = AuditStatus.WARNING
            else:
                overall_status = AuditStatus.PASS
                
            summary = f"Audit complete. Issues: {len(issues)} ({error_count} errors, {warning_count} warnings)."
            if error_count == 0 and warning_count == 0:
                summary = "All systems operational. OmniWeb is healthy."
            
            report = SystemAuditReport(
                overall_status=overall_status,
                summary=summary,
                issues=issues,
                metrics=metrics
            )
            
            # 6. Auto-Fix Analysis (Phase 8)
            fix_proposals = await fix_engine.analyze_report(report)
            metrics["fix_proposals_count"] = len(fix_proposals)
            
            # Log to Master Logbook
            try:
                await self._log_to_master(report, fix_proposals)
            except Exception as e:
                logger.error(f"Failed to log audit to master logbook: {e}")
            
            logger.info(f"--- System Audit Complete: {overall_status} ---")
            return report

    async def _audit_backend(self):
        issues = []
        metrics = {"backend_health": "stable"}
        
        # 1. Check module registry discovery
        try:
            from backend.core.module_registry import module_registry
            # Use discover_all_chips for a deep scan of the disk
            chips = module_registry.discover_all_chips()
            metrics["discovered_chips_count"] = len(chips)
            
            active_modules = module_registry.get_active_modules()
            metrics["mounted_modules_count"] = len(active_modules)
            
            for mod in active_modules:
                if mod.get("health") != "healthy":
                    issues.append(AuditIssue(
                        sector=AuditSector.BACKEND,
                        level=AuditStatus.WARNING,
                        message=f"Module {mod.get('slug', 'unknown')} is not healthy.",
                        details=mod
                    ))
        except Exception as e:
            issues.append(AuditIssue(
                sector=AuditSector.BACKEND,
                level=AuditStatus.ERROR,
                message=f"Module registry error: {str(e)}"
            ))

        # 2. Check AI Host Processors
        try:
            from backend.core.ai_host.command_router import ai_command_router
            processors = list(ai_command_router.registry._processors.keys())
            metrics["ai_processors"] = processors
            
            required_processors = ["knowledge", "memory", "graph", "supercommand", "logbook", "code_control"]
            for req in required_processors:
                if req not in processors:
                    issues.append(AuditIssue(
                        sector=AuditSector.BACKEND,
                        level=AuditStatus.ERROR,
                        message=f"Crucial AI Processor missing: {req}"
                    ))
        except Exception as e:
            issues.append(AuditIssue(
                sector=AuditSector.BACKEND,
                level=AuditStatus.ERROR,
                message=f"AI Host health check failed: {str(e)}"
            ))

        # 3. Check Patch System (AI Developer)
        ai_developer_files = [
            "backend/core/ai_developer/patch_generator.py",
            "backend/core/ai_developer/chip_editor.py",
            "backend/core/ai_developer/code_analyzer.py"
        ]
        for f in ai_developer_files:
            if not os.path.exists(f):
                 issues.append(AuditIssue(
                    sector=AuditSector.BACKEND,
                    level=AuditStatus.WARNING,
                    message=f"AI Developer component missing: {f}"
                ))

        # 4. Check for core files
        core_files = ["backend/main.py", "backend/core/database.py", "backend/core/config.py"]
        for f in core_files:
            if not os.path.exists(f):
                 issues.append(AuditIssue(
                    sector=AuditSector.BACKEND,
                    level=AuditStatus.ERROR,
                    message=f"Core backend file missing: {f}"
                ))
        
        return issues, metrics

    async def _audit_chips(self):
        issues = []
        metrics = {}
        
        chips_dir = "chips"
        if not os.path.exists(chips_dir):
            issues.append(AuditIssue(
                sector=AuditSector.CHIPS,
                level=AuditStatus.ERROR,
                message="Chips directory missing!"
            ))
            return issues, metrics
            
        folders = [d for d in os.listdir(chips_dir) if os.path.isdir(os.path.join(chips_dir, d))]
        metrics["total_chip_folders"] = len(folders)
        
        valid_chips = 0
        for folder in folders:
            if not folder.startswith("chip-"):
                continue
            
            manifest_path = os.path.join(chips_dir, folder, "chip.json")
            if not os.path.exists(manifest_path):
                issues.append(AuditIssue(
                    sector=AuditSector.CHIPS,
                    level=AuditStatus.WARNING,
                    message=f"Chip folder {folder} missing chip.json."
                ))
                continue
                
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    
                # Schema validation (OmniWeb v2 compatible)
                required_fields = ["name", "slug"]
                missing = [field for field in required_fields if field not in manifest]
                if missing:
                    issues.append(AuditIssue(
                        sector=AuditSector.CHIPS,
                        level=AuditStatus.ERROR,
                        message=f"Chip {folder} manifest missing required fields: {', '.join(missing)}"
                    ))
                
                # Check entry point (can be 'entry' or 'entry_frontend')
                entry = manifest.get("entry") or manifest.get("entry_frontend")
                if entry:
                    entry_path = os.path.join(chips_dir, folder, entry)
                    if not os.path.exists(entry_path):
                         issues.append(AuditIssue(
                            sector=AuditSector.CHIPS,
                            level=AuditStatus.ERROR,
                            message=f"Chip {folder} entry point missing on disk: {entry}"
                        ))
                    else:
                        valid_chips += 1
                else:
                    issues.append(AuditIssue(
                        sector=AuditSector.CHIPS,
                        level=AuditStatus.WARNING,
                        message=f"Chip {folder} has no entry point defined."
                    ))
                    
            except Exception as e:
                issues.append(AuditIssue(
                    sector=AuditSector.CHIPS,
                    level=AuditStatus.ERROR,
                    message=f"Error reading manifest for {folder}: {str(e)}"
                ))
        
        metrics["valid_chips_count"] = valid_chips
        return issues, metrics

    async def _audit_pwa(self):
        issues = []
        metrics = {}
        
        fe_dir = os.path.join("frontend", "shell")
        critical_files = ["index.html", "manifest.json", "sw.js"]
        
        for f in critical_files:
            path = os.path.join(fe_dir, f)
            if not os.path.exists(path):
                issues.append(AuditIssue(
                    sector=AuditSector.PWA,
                    level=AuditStatus.ERROR,
                    message=f"Critical PWA file missing: {f}"
                ))
            elif f == "manifest.json":
                try:
                    with open(path, 'r', encoding='utf-8') as mf:
                        manifest = json.load(mf)
                        metrics["pwa_name"] = manifest.get("name")
                        if "icons" not in manifest or not manifest["icons"]:
                             issues.append(AuditIssue(
                                sector=AuditSector.PWA,
                                level=AuditStatus.WARNING,
                                message="PWA manifest missing icons (Bad installability)."
                            ))
                except:
                    issues.append(AuditIssue(
                        sector=AuditSector.PWA,
                        level=AuditStatus.ERROR,
                        message="PWA manifest.json is invalid JSON."
                    ))
        
        return issues, metrics

    async def _audit_performance(self):
        issues = []
        metrics = {}
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            metrics["cpu_usage_percent"] = cpu_percent
            metrics["memory_rss_mb"] = mem_info.rss / (1024 * 1024)
            
            if cpu_percent > 90:
                issues.append(AuditIssue(
                    sector=AuditSector.PERFORMANCE,
                    level=AuditStatus.WARNING,
                    message=f"Critical CPU usage: {cpu_percent}%"
                ))
                
            if metrics["memory_rss_mb"] > 1536: # 1.5GB
                issues.append(AuditIssue(
                    sector=AuditSector.PERFORMANCE,
                    level=AuditStatus.WARNING,
                    message=f"High memory overhead: {metrics['memory_rss_mb']:.2f} MB"
                ))
        except:
            metrics["performance_monitoring"] = "system-blocked"

        # Check for AI pipeline cleanup (temp files)
        temp_dirs = ["temp", "tmp", "backend/runtime/temp"]
        total_temp_files = 0
        total_size = 0
        for d in temp_dirs:
            if os.path.exists(d):
                files = os.listdir(d)
                total_temp_files += len(files)
                for f in files:
                    f_path = os.path.join(d, f)
                    if os.path.isfile(f_path):
                        try: total_size += os.path.getsize(f_path)
                        except: pass
                
                if len(files) > 150:
                     issues.append(AuditIssue(
                        sector=AuditSector.PERFORMANCE,
                        level=AuditStatus.WARNING,
                        message=f"AI pipeline cleanup delay: {len(files)} files in {d}"
                    ))
        metrics["total_temp_files"] = total_temp_files
        metrics["temp_files_size_mb"] = total_size / (1024 * 1024)
            
        return issues, metrics

    async def _audit_frontend(self):
        issues = []
        metrics = {}
        
        fe_dir = os.path.join("frontend", "shell")
        required_components = {
            "shell": "index.html",
            "voice": "voice.js",
            "launcher": "main.js",
            "logbook": "logbook.js",
            "creator": "creator.js"
        }
        
        for name, filename in required_components.items():
            path = os.path.join(fe_dir, filename)
            if not os.path.exists(path):
                issues.append(AuditIssue(
                    sector=AuditSector.FRONTEND,
                    level=AuditStatus.WARNING,
                    message=f"Core UI component {name} ({filename}) missing."
                ))
            else:
                size = os.path.getsize(path)
                metrics[f"fe_{name}_size_kb"] = size / 1024
                if size == 0:
                    issues.append(AuditIssue(
                        sector=AuditSector.FRONTEND,
                        level=AuditStatus.ERROR,
                        message=f"Critical frontend asset {filename} is empty."
                    ))
        
        return issues, metrics

    async def _log_to_master(self, report: SystemAuditReport, fixes: List[AutoFixProposal] = []):
        """
        Creates an entry in the Master Logbook.
        """
        from backend.core.master_logbook.manager import master_logbook_manager
        from backend.core.master_logbook.models import MasterLogbookEntry, EntryType, Priority
        
        priority = Priority.MEDIUM
        if report.overall_status == AuditStatus.ERROR:
            priority = Priority.CRITICAL
        elif report.overall_status == AuditStatus.WARNING:
            priority = Priority.HIGH
            
        content = f"### 🛡️ System Audit Report - {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"**Overall Health:** {report.overall_status.value}\n\n"
        content += f"**Summary:** {report.summary}\n\n"
        
        if report.issues:
            content += "#### ⚠️ Issues Found:\n"
            for issue in report.issues:
                icon = "❌" if issue.level == AuditStatus.ERROR else "⚠️"
                content += f"- {icon} [{issue.sector.value}] **{issue.level.value}**: {issue.message}\n"
        else:
            content += "✅ All systems operating within normal parameters.\n"
        
        if fixes:
            content += "\n#### 🔧 Auto-Healing Proposals:\n"
            for f in fixes:
                content += f"- **{f.id}**: {f.analysis} (Actions: {len(f.actions)})\n"
            content += "\nUse `healing fix allow [id]` to apply.\n"

        content += "\n#### 📊 Performance Metrics:\n"
        for k, v in report.metrics.items():
            content += f"- **{k}**: {v}\n"
        
        entry = MasterLogbookEntry(
            type=EntryType.SYSTEM_AUDIT,
            content=content,
            priority=priority,
            metadata={
                "audit_report": report.model_dump(mode='json'),
                "status": report.overall_status.value
            }
        )
        master_logbook_manager.add_entry(entry)

auditor = SystemAuditor()
