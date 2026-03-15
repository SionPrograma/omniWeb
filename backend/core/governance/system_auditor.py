import os
import logging
import sqlite3
import time
from typing import Dict, List, Any
from backend.core.config import settings
from backend.core.module_registry import module_registry

logger = logging.getLogger(__name__)

class EngineeringAuditor:
    """
    High-discipline System Auditor for OmniWeb Governance.
    Executes aerospace-grade verification logic.
    """
    
    def __init__(self):
        self._audit_results: List[Dict[str, Any]] = []

    async def run_full_audit(self) -> Dict[str, Any]:
        """Executes a complete system scan."""
        self._audit_results = []
        logger.info("ENGINEERING AUDIT: Initializing Mission-Critical Scan...")

        # 1. Database Integrity
        self._audit_db()

        # 2. Service Registration
        self._audit_services()

        # 3. Integration Connectivity
        await self._audit_integration_layer()

        # 4. Dependency Health
        self._audit_dependencies()

        # 5. QR Gateway Status
        self._audit_qr_gateway()

        # Final Evaluation
        is_stable = all(r["status"] == "PASS" for r in self._audit_results)
        
        summary = {
            "timestamp": time.time(),
            "stability_status": "SYSTEM STABLE" if is_stable else "SYSTEM UNSTABLE",
            "critical_faults": [r for r in self._audit_results if r["status"] == "FAIL"],
            "checks": self._audit_results
        }
        
        logger.info(f"AUDIT COMPLETE: Status = {summary['stability_status']}")
        return summary

    def _audit_db(self):
        try:
            db_path = settings.DATABASE_URL
            conn = sqlite3.connect(db_path)
            res = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            status = "PASS" if res[0] == "ok" else "FAIL"
            self._audit_results.append({"sector": "database", "check": "integrity", "status": status, "details": res[0]})
        except Exception as e:
            self._audit_results.append({"sector": "database", "check": "integrity", "status": "FAIL", "details": str(e)})

    def _audit_services(self):
        active_count = len(module_registry.get_active_modules())
        discovered = module_registry.discover_all_chips()
        discovered_count = len(discovered)
        
        status = "PASS" if discovered_count > 0 else "FAIL"
        self._audit_results.append({
            "sector": "registry", 
            "check": "chips_discovered", 
            "status": status, 
            "details": f"{discovered_count} chips found on disk, {active_count} active in runtime"
        })

    async def _audit_integration_layer(self):
        try:
            from backend.core.integration_layer.integration_registry import integration_registry
            bridges = integration_registry.list_bridges()
            
            # If empty (script mode), check disk
            if not bridges:
                bridge_dir = "backend/core/integration_layer/bridges"
                if os.path.exists(bridge_dir):
                    files = [f for f in os.listdir(bridge_dir) if f.endswith(".py") and f != "__init__.py"]
                    bridges = [{"bridge_id": f} for f in files]

            status = "PASS" if len(bridges) > 0 else "FAIL"
            self._audit_results.append({
                "sector": "integration", 
                "check": "domain_bridges", 
                "status": status, 
                "details": f"{len(bridges)} bridges discovered/active"
            })
        except Exception as e:
            self._audit_results.append({"sector": "integration", "check": "health", "status": "FAIL", "details": str(e)})

    def _audit_dependencies(self):
        # Basic check for critical packages
        critical = ["fastapi", "sqlalchemy", "qrcode", "PIL"]
        missing = []
        for pkg in critical:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        
        status = "PASS" if not missing else "FAIL"
        self._audit_results.append({"sector": "infrastructure", "check": "dependencies", "status": status, "details": f"Missing: {missing}" if missing else "All critical pkgs found"})

    def _audit_qr_gateway(self):
        try:
            from backend.core.qr_gateway.qr_token_manager import qr_token_manager
            tokens = qr_token_manager.get_all_active_tokens()
            status = "PASS"
            self._audit_results.append({"sector": "security", "check": "qr_gateway", "status": status, "details": f"{len(tokens)} active tokens"})
        except Exception as e:
            self._audit_results.append({"sector": "security", "check": "qr_gateway", "status": "FAIL", "details": str(e)})

engineering_auditor = EngineeringAuditor()
