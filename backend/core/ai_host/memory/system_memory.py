import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class SystemMemory:
    """
    OmniWeb OS-like Memory Layer.
    Stores 'Working Memory' (Operational/Short-term) and 'Project Memory' (Continuity/Long-term).
    """
    def __init__(self, storage_path: str = "backend/data/system/memory.json"):
        # Use absolute path if possible, but for relative we assume root of project
        # In this env, project root is likely the Cwd.
        self.storage_path = os.path.abspath(storage_path)
        self._ensure_storage()
        self.data = self._load()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({
                    "working": {
                        "active_scope": None,
                        "last_important_file": None,
                        "last_operation_summary": None,
                        "workspace_state": "idle",
                        "last_update": datetime.now().isoformat()
                    },
                    "project": {
                        "roadmap_block": "Bloque 5",
                        "decisions": [],
                        "hard_rules": [
                            "Priorizar cambios mínimos y no destructivos.",
                            "Mantener trazabilidad absoluta por archivo.",
                            "No tocar CORE sin advertencia de impacto sistémico.",
                            "Validar que el Preview siempre permita retorno limpio."
                        ],
                        "sensitive_modules": [
                            "backend/core/ai_host/processors/proposal_processor.py",
                            "backend/core/ai_host/orchestration/cognitive_orchestrator.py",
                            "backend/core/execution/safety_policy.py"
                        ],
                        "last_applied_fix": None
                    }
                }, f, indent=4)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    # Working Memory
    def update_working(self, **kwargs):
        self.data["working"].update(kwargs)
        self.data["working"]["last_update"] = datetime.now().isoformat()
        self.save()

    def get_working(self) -> Dict[str, Any]:
        return self.data.get("working", {})

    def get_working_context(self) -> str:
        w = self.data.get("working", {})
        ctx = "CONTEXTO_OPERATIVO_RECIENTE:\n"
        ctx += f"- Último Archivo: {w.get('last_important_file', 'Ninguno')}\n"
        ctx += f"- Último Scope: {w.get('active_scope', 'Ninguno')}\n"
        if w.get('last_operation_summary'):
             ctx += f"- Última Acción: {w['last_operation_summary']}\n"
        ctx += f"- Estado del Workspace: {w.get('workspace_state', 'idle')}\n"
        return ctx

    # Project Memory
    def set_roadmap_block(self, block: str):
        self.data["project"]["roadmap_block"] = block
        self.save()

    def add_decision(self, decision: str):
        self.data["project"]["decisions"].append({
            "timestamp": datetime.now().isoformat(),
            "content": decision
        })
        self.save()

    def add_hard_rule(self, rule: str):
        if rule not in self.data["project"]["hard_rules"]:
            self.data["project"]["hard_rules"].append(rule)
            self.save()

    def add_sensitive_module(self, path: str):
        if path not in self.data["project"]["sensitive_modules"]:
            self.data["project"]["sensitive_modules"].append(path)
            self.save()

    def get_project_context(self) -> str:
        ctx = f"BLOQUE_ACTIVO: {self.data['project']['roadmap_block']}\n"
        if self.data["project"]["hard_rules"]:
            ctx += "REGLAS_DURAS_DETECTORAS:\n" + "\n".join([f"- {r}" for r in self.data["project"]["hard_rules"]]) + "\n"
        if self.data["project"]["sensitive_modules"]:
            ctx += "MÓDULOS_SENSIBLES_DETECTADOS:\n" + "\n".join([f"- {m}" for m in self.data["project"]["sensitive_modules"]]) + "\n"
        return ctx

# Singleton instance for the system
system_memory = SystemMemory()
