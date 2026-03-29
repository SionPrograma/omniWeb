
from typing import Dict, Any, List
import uuid

class SemanticTaskTree:
    """
    Semantic Task Tree Engine for OmniWeb AI Host.
    Decomposes a Mission into hierarchical layers, risks, and microtasks.
    Integration level: Block 8 (Semantic Decomposition).
    """

    LAYERS = {
        "workspace": "frontend/workspace",
        "memoria": "backend/core/ai_host/memory",
        "copiloto": "backend/core/ai_host/orchestration/copilot",
        "vocal": "backend/core/ai_host/voice_interface",
        "backend": "backend/core",
        "chip": "chips/chip-base"
    }

    DEPENDENCIES = {
        "frontend/workspace": ["backend/core/supercommand", "backend/core/system_state"],
        "backend/core/ai_host/memory": ["backend/core/database", "backend/core/ai_host/orchestration"],
        "backend/core/ai_host/orchestration/copilot": ["backend/core/ai_host/processors", "backend/core/ai_host/synthesis"],
        "chips/chip-base": ["backend/core/permissions", "backend/core/database"]
    }

    FORBIDDEN_ZONES = ["backend/core/security", "backend/core/auth", "backend/core/permissions"]

    def decompose(self, message: str, understanding: Dict[str, Any], lang: str = "es") -> Dict[str, Any]:
        """
        Main decomposition entry point.
        """
        msg_low = message.lower()
        
        # 1. Identify Primary Layer
        primary_layer = "desconocida"
        for key, path in self.LAYERS.items():
            if key in msg_low:
                primary_layer = path
                break
        
        # 2. Map Dependencies
        dependencies = self.DEPENDENCIES.get(primary_layer, ["No detectadas"])
        
        # 3. Assess Risk & Forbidden Sections
        forbidden = [z for z in self.FORBIDDEN_ZONES if z != primary_layer]
        risk = "MEDIO" if primary_layer != "desconocida" else "BAJO"
        if any(z in primary_layer for z in self.FORBIDDEN_ZONES):
            risk = "CRÍTICO"

        # 4. Generate Microtasks (Surgical & Small)
        microtasks = self._generate_microtasks(msg_low, primary_layer, lang)
        
        return {
            "mission_id": str(uuid.uuid4())[:8],
            "summary": f"Descomposición de misión: {message[:50]}...",
            "primary_layer": primary_layer,
            "affected_layers": [primary_layer] + dependencies if primary_layer != "desconocida" else ["General"],
            "dependencies": dependencies,
            "risk_level": risk,
            "forbidden_zones": forbidden,
            "microtasks": microtasks,
            "rationale": "Mapeo semántico de capas y dependencias sistémicas."
        }

    def _generate_microtasks(self, msg: str, layer: str, lang: str) -> List[str]:
        tasks = []
        if lang == "es":
            tasks.append(f"Auditar el estado actual de `{layer or 'módulo local'}`.")
            if "mejor" in msg or "fix" in msg:
                tasks.append("Evaluar impacto de cambios en capas vecinas.")
                tasks.append("Proponer microfix localizado sin afectar contratos estructurales.")
            elif "audit" in msg or "revis" in msg:
                tasks.append("Verificar coherencia de datos y logs.")
                tasks.append("Detectar deudas técnicas o fallos de performance.")
            else:
                tasks.append("Estabilizar entorno de ejecución.")
        else:
            tasks.append(f"Audit current state of `{layer or 'local module'}`.")
            tasks.append("Assess cross-layer dependencies.")
            tasks.append("Propose surgical micro-change.")
            
        return tasks[:3] # Max 3 microtasks

task_tree_engine = SemanticTaskTree()
