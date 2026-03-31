from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ScopeLock:
    """
    MEGAPROMPT EXECUTION LAYER - CAPA 2: SCOPE LOCK
    Prevents deviations and out-of-scope modifications.
    Ensures surgical precision and obedience to the Megaprompt.
    """
    def __init__(self, compiled_mission: Any):
        self.mission = compiled_mission
        self.allowed_surfaces = set(compiled_mission.target_surface)
        self.allowed_files = set(compiled_mission.critical_files)
        self.forbidden_zones = compiled_mission.forbidden_layers
        
    def validate_action(self, action_type: str, target: str, description: str) -> Dict[str, Any]:
        """
        Validates if an action is within the mission scope.
        Returns check result and rationale.
        """
        is_refactor = any(kw in description.lower() for kw in ["refactor", "limpiar", "cambio masivo", "reestructur", "clean up"])
        is_unrelated_fix = any(kw in description.lower() for kw in ["ya que estamos", "de paso", "aprovecho", "incidental", "fix colateral"])
        
        # 1. Check Technical Surface
        surface_ok = any(s in target.lower() for s in self.allowed_surfaces) if self.allowed_surfaces else True
        
        # 2. Check File Scope
        # If the mission lists specific files, we flag anything else
        file_ok = any(f in target for f in self.allowed_files) if self.allowed_files else True
        
        # 3. Check Forbidden Zones
        is_forbidden = any(z.lower() in target.lower() for z in self.forbidden_zones)
        
        # 4. Detect Intentional Drift
        has_drift = is_refactor or is_unrelated_fix
        
        violations = []
        if not surface_ok and target != "system":
            violations.append(f"Superficie '{target}' fuera de las capas permitidas: {self.allowed_surfaces}")
        if not file_ok and target not in ["system", "os"]:
             violations.append(f"Archivo '{target}' no mencionado en la misión original.")
        if is_forbidden:
             violations.append(f"Intento de modificar zona PROHIBIDA: {target}")
        if is_refactor:
             violations.append("Refactorización masiva detectada sin autorización explícita.")
        if is_unrelated_fix:
             violations.append("Detección de 'Scope Creep' (arreglos colaterales no pedidos).")

        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "risk_score": len(violations) * 0.25,
            "rationale": "Validación de alcance contra el Manifiesto de Misión." if not violations else "Desviación de misión detectada."
        }

class DeviationDetector:
    """
    MEGAPROMPT EXECUTION LAYER - CAPA 5: DEVIATION DETECTOR
    Compares the original mission with the proposed execution plan.
    """
    def check_drift(self, compiled_mission: Any, proposed_plan: List[Any]) -> Dict[str, Any]:
        logger.info("[DEVIATION_DETECTOR] Checking plan for mission drift...")
        lock = ScopeLock(compiled_mission)
        
        drifts = []
        for task in proposed_plan:
            # tasks could be ActionableTask (from task_planner) or ExecutionNode (from execution_tree)
            target = getattr(task, 'target_id', getattr(task, 'label', 'unknown'))
            desc = getattr(task, 'reason', getattr(task, 'description', ''))
            type = getattr(task, 'action_type', getattr(task, 'type', 'task'))
            
            check = lock.validate_action(type, target, desc)
            if not check["is_valid"]:
                drifts.extend(check["violations"])
                
        return {
            "has_drift": len(drifts) > 0,
            "drifts": drifts,
            "is_blocked": len(drifts) > 2 # Block if more than 2 violations
        }
