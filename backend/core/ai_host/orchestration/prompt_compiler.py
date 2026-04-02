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
    plan_steps: List[str] = Field(default_factory=list) # Phase 30: Dynamic Execution Tree
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
        
        lines = text.split('\n')
        
        # 1. Basic extraction via regex (Headers first)
        mission_match = re.search(r"(?:MISIÓN|MISSION):\s*(.*)", text, re.IGNORECASE)
        obj_match = re.search(r"(?:OBJETIVO|OBJECTIVE):\s*(.*)", text, re.IGNORECASE)
        
        # 2. Heuristic extraction if headers are missing
        if not mission_match and not obj_match:
            mission_name = lines[0].strip()[:60] + "..." if lines else "Misión Detectada"
            objective = text[:300] + "..."
        else:
            mission_name = mission_match.group(1).strip() if mission_match else "Misión Detectada"
            objective = obj_match.group(1).strip() if obj_match else text[:300]

        # 3. Detect Surfaces & Layers (Hardened mapping)
        layers_map = {
            "backend": ["core", "api", "database", "ai_host", "routing", "engine", "backend"],
            "frontend": ["workspace", "shell", "ui", "view", "component", "frontend", "cockpit", "interface"],
            "memory": ["mission", "semantic", "logbook", "history", "memory", "storage"],
            "orchestration": ["orchestrator", "brain", "cognitive", "reasoning", "director"],
            "multimodal": ["voice", "visual", "gesture", "multimodal", "evidence"]
        }
        
        detected_layers = []
        for layer, keywords in layers_map.items():
            if any(kw in text.lower() for kw in keywords):
                detected_layers.append(layer)

        # 4. ADVANCED BLOCK EXTRACTION (Prohibitions, Criteria, Risks)
        forbidden = []
        criteria = []
        risks = []
        
        # Block-based scanning
        current_block = None
        for line in lines:
            line_low = line.lower().strip()
            if not line_low: continue
            
            # Identify Block Start
            if any(kw in line_low for kw in ["no tocar", "no modificar", "forbidden", "don't touch", "prohibido", "restricci"]):
                current_block = "forbidden"
                continue
            elif any(kw in line_low for kw in ["éxito", "success", "criteria", "meta", "objetivo"]):
                current_block = "criteria"
                continue
            elif any(kw in line_low for kw in ["riesgo", "risk", "hazard", "caution", "warn"]):
                current_block = "risks"
                continue
            elif any(kw in line_low for kw in ["pasos", "steps", "flujo", "flow", "fases", "plan"]):
                current_block = "flow"
                continue
            
            # 1. Regex Match for sequential steps (e.g. "1. Do this")
            step_match = re.match(r"^(\d+)\.\s*(.*)", line.strip())
            if step_match:
                item = step_match.group(2).strip()
                if item:
                    plan_steps.append(item)
                    continue

            # 2. List-based collection
            if line.strip().startswith(("-", "*")) or (current_block and len(line) > 5):
                item = line.strip("-* ").strip()
                if not item: continue
                
                if current_block == "forbidden": forbidden.append(item)
                elif current_block == "criteria": criteria.append(item)
                elif current_block == "risks": risks.append(item)
                elif current_block == "flow": plan_steps.append(item)

        # 5. DETECT FILES (Regex hardened)
        files = re.findall(r"(?:[\w\/.-]+\/[\w.-]+\.[\w]+|[\w.-]+\.(?:py|js|css|html|md|json|ts))", text)
        files = list(set(files)) 

        # 6. AMBIGUITY CHECK (Technical Integrity)
        ambiguity = []
        if len(text) < 100:
            ambiguity.append("Megaprompt is too short for a complex mission.")
        if not detected_layers:
            ambiguity.append("Undefined operational layers (No surface match).")
        if not criteria and len(objective) < 50:
            ambiguity.append("Missing or vague success criteria.")

        mission = CompiledMission(
            mission_name=mission_name,
            primary_objective=objective,
            target_surface=detected_layers,
            allowed_layers=detected_layers,
            forbidden_layers=forbidden,
            critical_files=files,
            success_criteria=criteria or ["General mission success"],
            constraints=forbidden,
            risks_detected=risks,
            plan_steps=plan_steps,
            is_ambiguous=len(ambiguity) > 0,
            ambiguity_notes=ambiguity
        )
        
        logger.info(f"[PROMPT_COMPILER] Compiled: {mission.mission_name} | Sub-Tasks: {len(criteria)} | Risks: {len(risks)}")
        return mission

prompt_compiler = PromptCompiler()
