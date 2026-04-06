import logging
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class InterpretedCommand(BaseModel):
    goal: str
    constraints: List[str] = []
    target_modules: List[str] = []
    mission_scale: str = "component" # component, system, architecture
    analysis_depth: int = 1
    original_prompt: str
    risks: List[str] = []
    success_criteria: List[str] = []
    affected_layers: List[str] = []
    requires_decomposition: bool = False
    audit_only: bool = False
    conservative_mode: bool = False
    roadmap_first: bool = False
    forbidden_paths: List[str] = []
    forbidden_layers: List[str] = []
    allowed_paths: List[str] = []
    frozen_paths: List[str] = []
    frozen_layers: List[str] = []
    aggressiveness: str = "balanced" # surgical, balanced, ambitious
    source_draft_id: Optional[str] = None

class CommandInterpreter:
    """
    Hardened Creator Command Interpreter.
    Translates complex instructions into actionable mission parameters.
    """
    
    def __init__(self):
        self.module_keywords = {
            "routing": ["routing", "router", "rutas", "navegación", "navegacion"],
            "chat": ["chat", "mensajes", "conversación", "ui", "interfaz"],
            "auth": ["auth", "login", "permisos", "usuario", "gobierno"],
            "database": ["db", "db", "datos", "esquema", "modelos", "memoria"],
            "swarm": ["swarm", "shadow", "agentes", "paralelo", "orquestador"],
            "core": ["core", "host", "núcleo", "nucleo", "infra"]
        }

    async def interpret(self, prompt: str) -> InterpretedCommand:
        logger.info(f"[INTERPRETER] Analysing creator instruction: {prompt[:50]}...")
        
        msg = prompt.lower().strip()
        
        # 1. ROBUST GOAL EXTRACTION (Recursive pattern matching)
        goal = prompt
        # Priority 1: Multi-clause goals (Goal A AND Goal B)
        # We try to find the primary objective
        primary_match = re.split(r" and | y | además | además de ", prompt, maxsplit=1, flags=re.IGNORECASE)
        goal = primary_match[0].strip()
        
        # 2. ADVANCED CONSTRAINT DETECTION
        constraints = []
        constraint_patterns = [
            (r"without (breaking|affecting|changing|touching) (.*)", "Guard: {}"),
            (r"sin (romper|afectar|cambiar|tocar) (.*)", "Restricción: {}"),
            (r"no (rompas|afectes|cambies|toques) (.*)", "Límite: {}"),
            (r"only (.*)", "Scope limited to {}"),
            (r"solo (.*)", "Ámbito reducido a {}"),
            (r"evitá (.*)", "Evitar {}"),
            (r"avoid (.*)", "Avoid {}"),
            (r"excepto (.*)", "Exception: {}")
        ]
        
        # New Structured Constraint Detectors (Phase 19)
        forbidden_paths = []
        forbidden_layers = []
        allowed_paths = []
        aggressiveness = "balanced"
        
        # 2.1 PATH/FILE DETECTION
        # Patterns like: "no toques creator.js", "sin tocar el archivo css", "sin tocar backend/core"
        path_patterns = [
            r"(?:sin tocar|no toques|excepto|restringí|restringi|bloqueá|bloquea) (?:el archivo |la ruta |el path |la carpeta |el |la |)([\w\./\-\*]+)",
        ]
        for p in path_patterns:
            for match in re.finditer(p, msg, re.IGNORECASE):
                path = match.group(1).strip()
                if path and len(path) > 2:
                    forbidden_paths.append(path)
        
        # 2.2 LAYER DETECTION
        layer_map = {
            "ui": ["ui", "interfaz", "frontend", "visual"],
            "backend": ["backend", "api", "servidor", "server", "core"],
            "shell": ["shell", "terminal", "consola", "cockpit"],
            "css": ["css", "estilos", "styles", "diseño"],
            "db": ["db", "base de datos", "database", "modelos", "datos"],
            "auth": ["auth", "permisos", "login", "seguridad"],
            "navigation": ["navegación", "navegacion", "routing", "rutas"]
        }
        
        # Filtering reserved words from being detected as paths
        reserved_scope_words = ["auditó", "audita", "audit", "roadmap", "plan", "misión", "mision", "solo", "todo", "nada"]

        # Detecting: "no toques la ui", "solo backend", "bloqueá el backend"
        for layer, keywords in layer_map.items():
            if any(re.search(rf"(?:sin tocar|no toques|bloque[áa]|restring[íi]|no (?:afectes|cambies|rompas)) (?:la |el |){k}", msg, re.IGNORECASE) for k in keywords):
                forbidden_layers.append(layer)
            if any(re.search(rf"\b(?:solo|únicamente|unicamente)\b (?:en |la |el |){k}\b", msg, re.IGNORECASE) for k in keywords):
                # If "solo backend", then UI and Shell are forbidden (inverted logic)
                for l in layer_map.keys():
                    if l != layer: forbidden_layers.append(l)

        # 2.3 ALLOWED PATHS
        # Patterns like: "tocá solo el editor", "solo en backend/core"
        allowed_patterns = [
            r"(?:solo|únicamente|unicamente) (?:en |tocá |toca |)(?:el archivo |la ruta |el path |la carpeta |)([\w\./\-\*]+)",
        ]
        for p in allowed_patterns:
            for match in re.finditer(p, msg, re.IGNORECASE):
                path = match.group(1).strip()
                if path and len(path) > 2 and path not in reserved_scope_words and path not in layer_map.keys():
                    allowed_paths.append(path)

        # 2.3.1 FROZEN DETECTION (Phase 21: Sectorial Freeze)
        frozen_paths = []
        frozen_layers = []
        freeze_patterns = [
            r"(?:congel[áa]|paus[áa]|freeze) (?:el archivo |la ruta |el path |la carpeta |el |la |)([\w\./\-\*]+)",
        ]
        for p in freeze_patterns:
            for match in re.finditer(p, msg, re.IGNORECASE):
                path = match.group(1).strip()
                if path and len(path) > 2 and path not in reserved_scope_words:
                    if any(path in keywords for keywords in layer_map.values()):
                        # Try to find the layer key
                        for l, keywords in layer_map.items():
                            if path in keywords: frozen_layers.append(l); break
                    else:
                        frozen_paths.append(path)

        # 2.4 AGGRESSIVENESS
        if any(w in msg for w in ["quirúrgico", "quirurgico", "mínimo", "minimo", "parche"]):
            aggressiveness = "surgical"
        elif any(w in msg for w in ["ambicioso", "refactor", "limpiar todo", "mejorar todo"]):
            aggressiveness = "ambitious"
        elif "conservador" in msg:
            aggressiveness = "surgical"

        # 2.5 SOURCE DRAFT EXTRACTION (Phase 113 Traceability)
        source_draft_id = None
        draft_match = re.search(r"--source_draft=([\w\-]+)", prompt, re.IGNORECASE)
        if draft_match:
            source_draft_id = draft_match.group(1).strip()

        
        for pattern, template in constraint_patterns:
            matches = re.finditer(pattern, msg, re.IGNORECASE)
            for m in matches:
                if len(m.groups()) > 1:
                     constraints.append(template.format(m.group(2).strip()))
                else:
                     constraints.append(template.format(m.group(1).strip()))
        
        # 3. TECHNICAL TARGET DISCOVERY
        targets = []
        for mod, keywords in self.module_keywords.items():
            if any(k in msg for k in keywords):
                targets.append(mod)
        if not targets:
            targets = ["core"]
            
        # 4. SCALE & DEPTH ANALYSIS
        scale = "component"
        depth = 1
        
        if any(w in msg for w in ["sistema", "system", "todo", "global"]):
            scale = "system"
            depth = 2
        if any(w in msg for w in ["arquitectura", "architecture", "estilo", "diseño base"]):
            scale = "architecture"
            depth = 3
            
        # 5. SPECIAL DIRECTIVE: MISSION HARDENING
        if "hardening" in msg or "blindaje" in msg or "proteg" in msg:
             depth = 3
             constraints.append("Priority: Stability & Integrity")
             
        # 6. RISK & SUCCESS CRITERIA ANALYSIS (New Intake Layer)
        risks = []
        success_criteria = []
        affected_layers = targets # Default to targets
        
        # New Operational Flags
        audit_only = any(w in msg for w in ["solo auditá", "solo audita", "inspeccioná", "audit only"])
        conservative_mode = any(w in msg for w in ["conservador", "sin romper", "prudente", "despacio"])
        roadmap_first = any(w in msg for w in ["antes del plan", "ver roadmap", "mostrame el roadmap"])

        # Enhanced Success Criteria Extraction
        criteria_patterns = [
            (r"para que (.*)", "Success: Component {}"),
            (r"debería (.*)", "Prop: Should {}"),
            (r"objective: (.*)", "Goal: {}")
        ]
        for pattern, template in criteria_patterns:
            matches = re.finditer(pattern, msg, re.IGNORECASE)
            for m in matches:
                success_criteria.append(template.format(m.group(1).strip()))

        is_mission = msg.startswith("mission:") or any(w in msg for w in ["implementá", "arreglá", "creá"])
        if is_mission:
             # Deep analysis for mission prompts
             depth = max(depth, 2)
             if not success_criteria:
                  success_criteria.append("Visible result in UI/Dashboard")
             if len(msg) > 80:
                  requires_decomp = True
             
        if "borra" in msg or "delete" in msg or "rompe" in msg:
             risks.append("Potential data loss or architectural breakage")
             
        if "migra" in msg or "db" in msg:
             risks.append("Schema instability or service downtime")
             
        # Result Mapping
        interpreted = InterpretedCommand(
            goal=goal.strip(),
            constraints=constraints,
            target_modules=targets,
            mission_scale=scale,
            analysis_depth=depth,
            original_prompt=prompt,
            risks=risks,
            success_criteria=success_criteria,
            affected_layers=affected_layers,
            requires_decomposition=is_mission or depth >= 2,
            audit_only=audit_only,
            conservative_mode=conservative_mode,
            roadmap_first=roadmap_first,
            forbidden_paths=list(set(forbidden_paths)),
            forbidden_layers=list(set(forbidden_layers)),
            allowed_paths=list(set(allowed_paths)),
            frozen_paths=list(set(frozen_paths)),
            frozen_layers=list(set(frozen_layers)),
            aggressiveness=aggressiveness,
            source_draft_id=source_draft_id
        )
        
        logger.info(f"[INTERPRETER] Result -> Goal: {interpreted.goal} | Scale: {scale} | Constr: {len(constraints)}")
        return interpreted

command_interpreter = CommandInterpreter()
