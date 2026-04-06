import logging
import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
from backend.core.ai_host.memory.handoff_manager import handoff_manager

logger = logging.getLogger(__name__)

class SimulationMetric(BaseModel):
    category: str # REBASE, GOVERNANCE, SYNC, PERSONA
    score: float # 0.0 to 1.0 (Higher means more friction)
    description: str

class ProjectedState(BaseModel):
    domain: str
    friction_index: float
    bottleneck_risk: str # LOW, MED, HIGH, CRITICAL
    rationale: str

class RoadmapScenario(BaseModel):
    scenario_id: str
    name: str
    type: str # CURRENT, OPTIMIZED, AGGRESSIVE, CONSERVATIVE
    projected_friction: List[SimulationMetric]
    domain_forecasts: List[ProjectedState]
    confidence: float
    summary: str
    recommendations: List[str]

class StrategicSimulator:
    """
    OMNIWEB — BLOQUE: STRATEGIC SIMULATION MODE.
    Projects roadmap friction before execution.
    """
    
    def __init__(self):
        pass

    def generate_scenarios(self, branch_id: str = "main") -> List[RoadmapScenario]:
        macro = roadmap_aggregator.get_macro_roadmap(branch_id=branch_id)
        # macro is a CognitiveRoadmap object, we need its groups
        groups = [g.model_dump() for g in macro.groups]
        
        scenarios = []
        
        # 1. CURRENT SCENARIO (As is)
        current_sim = self._simulate_sequence(groups, "CURRENT")
        scenarios.append(current_sim)
        
        # 2. OPTIMIZED SCENARIO (Readiness-based)
        # We sort groups by readiness score for the simulation
        optimized_groups = sorted(groups, key=lambda x: x.get("launch_readiness", 0), reverse=True)
        optimized_sim = self._simulate_sequence(optimized_groups, "OPTIMIZED")
        scenarios.append(optimized_sim)
        
        return scenarios

    def _simulate_sequence(self, groups: List[Dict], s_type: str) -> RoadmapScenario:
        domain_forecasts = []
        rebase_pressure = 0.0
        gov_friction = 0.0
        
        # Heuristics for simulation
        for g in groups:
            domain = g.get("group_id", "unknown")
            readiness = g.get("launch_readiness", 0.0)
            risk = g.get("risk_density", 0.1)
            blocked_count = g.get("blocked_count", 0)
            
            # Domain friction projection
            f_index = (1.0 - readiness) * 0.5 + (risk * 0.5)
            if blocked_count > 0: f_index += 0.2
            
            b_risk = "LOW"
            if f_index > 0.4: b_risk = "MED"
            if f_index > 0.7: b_risk = "HIGH"
            if f_index > 0.9: b_risk = "CRITICAL"
            
            domain_forecasts.append(ProjectedState(
                domain=domain,
                friction_index=min(1.0, f_index),
                bottleneck_risk=b_risk,
                rationale=f"Readiness de {int(readiness*100)}% y riesgo acumulado de {int(risk*100)}%."
            ))
            
            # Aggregated Metrics
            rebase_pressure += risk * 0.3
            gov_friction += (blocked_count / 10.0) if blocked_count > 0 else 0.0

        # Confidence logic
        confidence = 0.9 if s_type == "CURRENT" else 0.7
        if any(g.get("launch_readiness", 0) == 0 for g in groups):
            confidence -= 0.2 # Lower confidence if domains are empty/fresh

        sid = hashlib.md5(f"sim:{s_type}:{datetime.now()}".encode()).hexdigest()[:8]
        
        metrics = [
            SimulationMetric(category="REBASE", score=min(1.0, rebase_pressure), description="Presión de rebase proyectada."),
            SimulationMetric(category="GOVERNANCE", score=min(1.0, gov_friction), description="Carga de autoridad y bloqueos de PIN.")
        ]
        
        # Recommendations
        recommendations = []
        if rebase_pressure > 0.5: recommendations.append("Reordenar misiones de alto riesgo para evitar colisiones atómicas.")
        if gov_friction > 0.4: recommendations.append("Asegurar disponibilidad de PIN de Creador para liberar cuellos de botella.")
        if s_type == "CURRENT" and rebase_pressure > 0.7: recommendations.append("ADVERTENCIA: La secuencia actual garantiza rebases en cascada.")

        summary = f"Simulación {s_type}: Se proyecta un riesgo {b_risk} de estancamiento táctico."
        if s_type == "OPTIMIZED":
            summary = "Simulación Optimizada: Reduce la presión de rebase al priorizar dominios con mayor readiness."

        return RoadmapScenario(
            scenario_id=sid,
            name=f"Escenario {s_type.capitalize()}",
            type=s_type,
            projected_friction=metrics,
            domain_forecasts=domain_forecasts,
            confidence=max(0.0, confidence),
            summary=summary,
            recommendations=recommendations
        )

strategic_simulator = StrategicSimulator()
