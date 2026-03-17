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
    original_prompt: str

class CommandInterpreter:
    """
    Translates creator instructions into structured mission intent.
    Identifies goals, constraints, and affected systems.
    """
    
    def __init__(self):
        self.module_keywords = {
            "routing": ["routing", "router", "rutas", "navegación"],
            "chat": ["chat", "mensajes", "conversación", "ui"],
            "auth": ["auth", "login", "permisos", "usuario"],
            "database": ["db", "db", "datos", "esquema", "modelos"],
            "swarm": ["swarm", "shadow", "agentes", "paralelo"]
        }

    async def interpret(self, prompt: str) -> InterpretedCommand:
        logger.info(f"[INTERPRETER] Analysing creator command: {prompt}")
        
        msg = prompt.lower().strip()
        
        # 1. EXTRACT GOAL
        goal = prompt
        goal_keywords = ["improve", "fix", "update", "optimize", "mejora", "corrige", "actualiza", "optimiza"]
        for kw in goal_keywords:
            if kw in msg:
                # Extract everything after the keyword but before any constraint
                parts = re.split(r" without | sin | no | but | pero ", prompt, flags=re.IGNORECASE)
                goal = parts[0].strip()
                break
        
        # 2. DETECT CONSTRAINTS
        constraints = []
        constraint_patterns = [
            (r"without breaking (.*)", "Do not break {}"),
            (r"without affecting (.*)", "Do not affect {}"),
            (r"sin romper (.*)", "No romper {}"),
            (r"sin afectar (.*)", "No afectar {}"),
            (r"no rompas (.*)", "No rompas {}"),
            (r"no afectes (.*)", "No afectes {}")
        ]
        
        for pattern, template in constraint_patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                constraints.append(template.format(match.group(1).strip()))
                
        # Fallback for simple "sin X"
        if not constraints:
            if " sin " in msg:
                constraints.append(f"No afectar {msg.split(' sin ', 1)[1].strip()}")
            elif " without " in msg:
                constraints.append(f"Do not affect {msg.split(' without ', 1)[1].strip()}")
            
        # 3. DETECT TARGET MODULES
        targets = []
        for mod, keywords in self.module_keywords.items():
            if any(k in msg for k in keywords):
                targets.append(mod)
        if not targets:
            targets = ["core"] # Default target
            
        # 4. DETERMINE MISSION SCALE
        scale = "component"
        if any(w in msg for w in ["sistema", "system", "plataforma", "platform", "ecosistema", "ecosystem"]):
            scale = "system"
        if any(w in msg for w in ["arquitectura", "architecture", "estilo", "infraestructura", "infrastructure"]):
            scale = "architecture"

        interpreted = InterpretedCommand(
            goal=goal.strip(),
            constraints=constraints,
            target_modules=targets,
            mission_scale=scale,
            original_prompt=prompt
        )
        
        logger.info(f"[INTERPRETER] Interpretation complete: {interpreted.goal} (Scale: {scale})")
        return interpreted

command_interpreter = CommandInterpreter()
