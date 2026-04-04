import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .mission_models import MissionState, MissionHandoff, MissionStatus, MissionCompactDigest

logger = logging.getLogger(__name__)

class MissionSummarizer:
    """
    Expert system for distilling MissionState into an operational Handoff.
    Converts raw technical metadata into structured narrative.
    """
    
    def summarize(self, mission: MissionState) -> MissionHandoff:
        logger.info(f"[MISSION_SUMMARIZER] Generating final executive briefing for {mission.mission_id}...")
        
        # 1. Timeline & Milestones
        milestones = self._extract_milestones(mission)
        
        # 2. Executive Summary & Impact
        summary = self._generate_executive_summary(mission, milestones)
        impact = self._generate_technical_impact_summary(mission)
        decisions = self._extract_key_decisions(mission)
        
        # 3. Governance & Recovery
        gov = mission.context_snap.get("governance_health", {"score": 1.0, "incidents": 0})
        recovery = [r for r in mission.blocked_reasons if "RESCATE" in r or "RECOVERY" in r or "BLOQUEO" in r]
        
        # 4. Multimodal Context
        evidence_ids = [h.get("id") for h in mission.multimodal_history if h.get("event") == "INITIAL_CAPTURE"]
        
        # 5. Next Steps (Heuristics)
        next_steps = self._suggest_next_steps(mission)
        
        briefing_title = f"Reporte de Misión: {mission.active_goal[:40]}..." if len(mission.active_goal) > 40 else f"Reporte: {mission.active_goal}"

        handoff = MissionHandoff(
            mission_id=mission.mission_id,
            briefing_title=briefing_title,
            goal=mission.active_goal,
            executive_summary=summary,
            key_decisions=decisions,
            technical_impact=impact,
            timeline_milestones=milestones,
            governance_footprint=gov,
            multimodal_evidence_refs=evidence_ids,
            recovery_events=recovery,
            final_status=mission.status,
            next_steps=next_steps,
            payload={
                "last_active_targets": mission.related_targets,
                "conservative_mode": mission.parameters.get("conservative_mode", False),
                "visual_diagnosis": mission.visual_context.get("hypothesis", {}) if mission.visual_context else {}
            }
        )
        
        return handoff

    def _extract_key_decisions(self, mission: MissionState) -> List[str]:
        """Extracts high-stakes decisions from mission history."""
        decisions = []
        for h in mission.multimodal_history:
            if h.get("event") == "GATE_DECISION":
                decisions.append(f"Gate Decision: {h.get('status')} - '{h.get('reason', 'Sin motivo')}'")
            elif h.get("event") == "RE_ORIENTATION":
                decisions.append("Re-orientación: Ajuste de foco geográfico por inconsistencia visual.")
            elif h.get("event") == "CHECKPOINT_ROLLBACK":
                decisions.append(f"Rollback: Retorno a checkpoint {h.get('checkpoint_id')} tras fallo en validación.")
        
        if mission.parameters.get("conservative_mode"):
            decisions.append("Modo Conservador: Ejecución restrictiva activada por defecto.")
            
        return decisions

    def _generate_technical_impact_summary(self, mission: MissionState) -> str:
        """Synthesizes the technical result from steps and evidence."""
        count = len(mission.completed_steps)
        targets = ", ".join(mission.related_targets) or "recursos globales"
        
        impact = f"Se completaron {count} intervenciones técnicas sobre {targets}."
        
        if mission.visual_context and "hypothesis" in mission.visual_context:
            impact += f"\nImpacto multimodal: {mission.visual_context['hypothesis'].get('remediation_summary', 'Diagnóstico aplicado.')}"
            
        if mission.status == MissionStatus.COMPLETED:
            impact += "\nResultado: Objetivo alcanzado con integridad verificada."
        elif mission.status == MissionStatus.BLOCKED:
             impact += "\nResultado: Interrupción por política de seguridad (Gobernanza)."
        
        return impact


    def create_compact_digest(self, mission: MissionState) -> MissionCompactDigest:
        """
        Creates a high-density operational summary for the cockpit and focus switching.
        """
        logger.debug(f"[MISSION_SUMMARIZER] Creating compact digest for {mission.mission_id}...")
        
        # 1. Goal Compact
        goal_c = (mission.active_goal[:120] + '...') if len(mission.active_goal) > 123 else mission.active_goal
        
        # 2. Constraints
        constraints = []
        p = mission.parameters
        if p.get("forbidden_paths"): constraints.append(f"Paths Restringidos: {len(p['forbidden_paths'])}")
        if p.get("frozen_layers"): constraints.append(f"Capas Congeladas: {len(p['frozen_layers'])}")
        if p.get("conservative_mode"): constraints.append("Modo Conservador")
        
        # 3. Governance
        gov = mission.context_snap.get("governance_health", {"score": 1.0})
        latest_inc = mission.blocked_reasons[-1] if mission.blocked_reasons else None
        
        # 4. Continuity
        next_hint = self._suggest_next_steps(mission)[0] if self._suggest_next_steps(mission) else "Continuarroadmap"
        
        # 5. Multimodal
        multi = None
        if mission.visual_context and "hypothesis" in mission.visual_context:
            h = mission.visual_context["hypothesis"]
            remed = h.get('remediation_summary', 'Diagnóstico pendiente')
            multi = (remed[:80] + '...') if len(remed) > 83 else remed

        return MissionCompactDigest(
            mission_id=mission.mission_id,
            goal_compact=goal_c,
            status_label=mission.status.value,
            active_constraints=constraints,
            governance_score=gov.get("score", 1.0),
            latest_incident=latest_inc,
            next_step_hint=next_hint,
            multimodal_summary=multi,
            readiness=mission.readiness_state if hasattr(mission, 'readiness_state') else "READY",
            updated_at=datetime.now()
        )

    def _extract_milestones(self, mission: MissionState) -> List[str]:
        steps = []
        if mission.completed_steps:
             steps.append(f"✓ {len(mission.completed_steps)} tareas completadas.")
             
        for h in mission.multimodal_history:
            if h.get("event") == "INITIAL_CAPTURE":
                steps.append(f"📸 Diagnóstico visual inicial.")
            elif h.get("event") == "RE_ORIENTATION":
                 steps.append(f"🎯 Foco corregido geométricamente.")
            elif h.get("event") == "GATE_DECISION":
                 status = h.get("status", "UNKNOWN")
                 if status == "BLOCKED_BY_RISK":
                      steps.append(f"🛡️ Bloqueo de Gobernanza.")
        return steps

    def _generate_executive_summary(self, mission: MissionState, milestones: List[str]) -> str:
        targets = ", ".join(mission.related_targets) or "Varios"
        status_text = "completada" if mission.status == MissionStatus.COMPLETED else "activa"
        summary = f"Intervención en '{targets}' ({status_text})."
        if mission.visual_context: summary += f" Con guía multimodal."
        return summary

    def _suggest_next_steps(self, mission: MissionState) -> List[str]:
        steps = []
        if mission.status == MissionStatus.COMPLETED:
             steps.append("Validación final de integridad.")
        elif mission.status == MissionStatus.BLOCKED:
             steps.append("Revisión de bloqueos de gobernanza.")
        else:
             steps.append("Ejecutar siguiente paso del roadmap.")
        return steps

mission_summarizer = MissionSummarizer()
