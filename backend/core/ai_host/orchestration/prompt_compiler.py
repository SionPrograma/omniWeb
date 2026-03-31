from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import re
import logging

logger = logging.getLogger(__name__)

class CompiledMission(BaseModel):
    mission_name: str = "Nueva Misión"
    primary_objective: str
    target_surface: List[str] = Field(default_factory=list)
    allowed_layers: List[str] = Field(default_factory=list)
    forbidden_layers: List[str] = Field(default_factory=list)
    critical_files: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    risks_detected: List[str] = Field(default_factory=list)
    is_ambiguous: bool = False
    ambiguity_notes: List[str] = Field(default_factory=list)

class PromptCompiler:
    """
    MEGAPROMPT EXECUTION LAYER - CAPA 1: PROMPT COMPILER
    Transforms long, complex creator prompts into a structured mission manifesto.
    Disciplines the input to prevent drift and scope creep.
    """

    def compile(self, text: str) -> CompiledMission:
        logger.info("[PROMPT_COMPILER] Compiling megaprompt...")
        
        # 1. Basic extraction via regex (looking for standard headers in megaprompts)
        mission_match = re.search(r"(?:MISIÓN|MISSION):\s*(.*)", text, re.IGNORECASE)
        obj_match = re.search(r"(?:OBJETIVO|OBJECTIVE):\s*(.*)", text, re.IGNORECASE)
        
        # 2. Heuristic extraction if headers are missing
        if not mission_match and not obj_match:
            # First 100 chars as mission name
            mission_name = text.split('\n')[0][:50] + "..."
            objective = text[:200] + "..."
        else:
            mission_name = mission_match.group(1).strip() if mission_match else "Misión Detectada"
            objective = obj_match.group(1).strip() if obj_match else text[:200]

        # 3. Detect Surfaces & Layers
        layers_map = {
            "backend": ["core", "api", "database", "ai_host", "routing"],
            "frontend": ["workspace", "shell", "ui", "view", "component"],
            "memory": ["mission", "semantic", "logbook", "history"],
            "orchestration": ["orchestrator", "brain", "cognitive"],
            "multimodal": ["voice", "visual", "gesture"]
        }
        
        detected_layers = []
        for layer, keywords in layers_map.items():
            if any(kw in text.lower() for kw in keywords):
                detected_layers.append(layer)

        # 4. Detect Prohibitions (Forbidden Zones)
        forbidden = []
        prohibition_keywords = ["no tocar", "no modificar", "sin tocar", "forbidden", "don't touch", "prohibido"]
        for line in text.split('\n'):
            if any(kw in line.lower() for kw in prohibition_keywords):
                forbidden.append(line.strip())

        # 5. Detect Files
        # Look for patterns like "archivo.py" or "/path/to/file"
        files = re.findall(r"[\w\/\.-]+\.(?:py|js|css|html|md|json)", text)
        files = list(set(files)) # unique

        # 6. Ambiguity Check
        ambiguity = []
        if len(text) < 50:
            ambiguity.append("Prompt demasiado corto para una misión compleja.")
        if not detected_layers:
            ambiguity.append("No se detectaron capas de superficie claras.")

        mission = CompiledMission(
            mission_name=mission_name,
            primary_objective=objective,
            target_surface=detected_layers,
            allowed_layers=detected_layers,
            forbidden_layers=forbidden,
            critical_files=files,
            success_criteria=["Ejecución del árbol sin desviaciones", "Validación de cada microtarea"],
            constraints=forbidden,
            is_ambiguous=len(ambiguity) > 0,
            ambiguity_notes=ambiguity
        )
        
        logger.info(f"[PROMPT_COMPILER] Mission Compiled: {mission.mission_name} | Files: {len(files)}")
        return mission

prompt_compiler = PromptCompiler()
