
import logging
import uuid
from typing import Dict, Any, Optional
from .base import CommandProcessor, AICommandResponse
from ..memory.mission_manager import mission_manager, MissionState, MissionStatus

logger = logging.getLogger(__name__)

class MultimodalProcessor(CommandProcessor):
    """
    Handles missions initiated via visual evidence (screenshots, annotations).
    Bridges the gap between 'Show' and 'Act'.
    """

    async def can_handle(self, command: str) -> bool:
        return "[VISUAL_EVIDENCE]" in command

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        logger.info("[MULTIMODAL_PROCESSOR] Processing visual evidence...")
        from datetime import datetime
        
        # 1. Extract Evidence Details
        evidence_text = msg.replace("[VISUAL_EVIDENCE]", "").strip()
        context = context or {}
        evidence_entry = context.get("multimodal_evidence", [{}])[0]
        image_url = evidence_entry.get("data", "local_capture") # Evidence data is in 'data' field (Base64)
        media_id = evidence_entry.get("id", "unknown")
        annotations = evidence_entry.get("annotations", [])
        
        # Simulate Vision Intelligence (Phase 21: Hypothesis Generation)
        hypothesis = self._generate_visual_hypothesis(evidence_text, annotations)
        
        # 2. Bind to Mission & Calculate Visual Diff
        active = mission_manager.get_active_mission()
        
        # ERGONOMICS: Detect if the user wants to branch or start fresh
        force_new = any(kw in (evidence_text or "").lower() for kw in ["nueva misión", "new mission", "otra misión", "separar"])
        if force_new and active:
             logger.info("[MULTIMODAL_PROCESSOR] Creator requested a separate mission. Closing current and starting fresh.")
             mission_manager.close_current_mission("Branching into new visual mission.")
             active = None

        visual_diff = None
        if active and active.visual_context:
            visual_diff = self._calculate_visual_diff(active.visual_context.get("annotations", []), annotations)
            # Annotate internal hypothesis shift
            prev_hyp = active.visual_context.get("hypothesis", {})
            if prev_hyp.get("layer") != hypothesis.get("layer"):
                hypothesis["shift_detected"] = f"Shift operacional: de {prev_hyp.get('layer')} a {hypothesis.get('layer')}"
                if visual_diff: visual_diff["hypothesis_shift"] = True

        target_goal = f"Analizar evidencia visual: {evidence_text}"
        
        visual_ctx = {
            "media_id": media_id,
            "source_image": image_url,
            "annotations": annotations,
            "hypothesis": hypothesis,
            "visual_diff": visual_diff
        }
        
        if not active:
            mission = mission_manager.create_mission(target_goal)
            mission.visual_context = visual_ctx
            mission.parameters["audit_only"] = True
            
            # CAPA 3: Update related targets to focus the swarm
            if hypothesis.get("layer"):
                 mission.related_targets.append(hypothesis["layer"])
            for path in hypothesis.get("suggested_paths", []):
                 if path not in mission.related_targets:
                      mission.related_targets.append(path)

            # Initial History Entry (PHASE 55: SIGNAL FILTERING)
            mission.multimodal_history.append({
                "id": str(uuid.uuid4()),
                "event": "INITIAL_CAPTURE",
                "timestamp": datetime.now().isoformat(),
                "hypothesis": hypothesis,
                "annotations": annotations,
                "visual_diff": None,
                "relevance": "CRITICAL" # Newest is always critical
            })
            
            mission_manager.save_mission(mission)
            
            res_msg = (
                f"📸 **EVIDENCIA VISUAL RECIBIDA**\n"
                f"Hipótesis inicial: {hypothesis['description']}\n"
                f"Capa probablemente afectada: `{hypothesis['layer']}`"
            )
        else:
            active.visual_context = visual_ctx
            active.context_snap["operational_context"] = "CORRECTION" if (visual_diff and visual_diff.get("has_shift")) else "REORIENT"
            
            # CAPA 2 & 3: Re-orient existing mission targets
            if hypothesis.get("layer") and hypothesis["layer"] not in active.related_targets:
                 active.related_targets.append(hypothesis["layer"])
            for path in hypothesis.get("suggested_paths", []):
                 if path not in active.related_targets:
                      active.related_targets.append(path)

            # Record Re-orientation in History (PHASE 55: PRUNING)
            # Downgrade previous signals to SUPPORT
            for h in active.multimodal_history:
                if h.get("relevance") == "CRITICAL":
                    h["relevance"] = "SUPPORT"
                    
            active.multimodal_history.append({
                "id": str(uuid.uuid4()),
                "event": "RE_ORIENTATION",
                "timestamp": datetime.now().isoformat(),
                "hypothesis": hypothesis,
                "annotations": annotations,
                "visual_diff": visual_diff,
                "creator_comment": evidence_text,
                "relevance": "CRITICAL" # Fresh re-orientation takes precedence
            })
            
            mission_manager.save_mission(active)
            
            # CAPA 2: Archival Recovery (PHASE 56)
            recovered = active.search_archived_evidence(hypothesis, limit=1)
            recovery_note = ""
            if recovered:
                r = recovered[0]
                reason = r["retrieval_metadata"]["match_reason"]
                recovery_note = f"\n\n[🔄 MEMORIA RECUPERADA: Se reactivó evidencia previa por {reason}]"
            
            res_msg = (
                f"📎 **RE-ORIENTACIÓN VISUAL COMPLETADA**\n"
                f"Nueva Hipótesis: {hypothesis['description']}\n"
                f"Foco desplazado según corrección del Creador.{recovery_note}"
            )
            if visual_diff and visual_diff.get("has_shift"):
                 res_msg += f"\n\n[Δ VISUAL VALIDADO: +{visual_diff['added_count']}, -{visual_diff['removed_count']}]"

        return AICommandResponse(
            intent="visual_mission",
            status="success",
            message=res_msg,
            payload={
                "hypothesis": hypothesis,
                "visual_context": visual_ctx,
                "visual_diff": visual_diff,
                "technical_orientation": {
                    "layer": hypothesis.get("layer"),
                    "component": hypothesis.get("component"),
                    "route": hypothesis.get("route"),
                    "issue_type": hypothesis.get("issue_type"),
                    "confidence": hypothesis.get("confidence", "low")
                },
                "action": "activate_multimodal_pipeline"
            }
        )

    def _calculate_visual_diff(self, prev_ann: list, curr_ann: list) -> Dict[str, Any]:
        """
        CAPA 2: Generates a geometric comparison between two versions of focus.
        Identifies added, removed and persistent points/boxes.
        """
        def get_key(a): return f"{a.get('type')}_{round(a.get('x',0), 2)}_{round(a.get('y',0), 2)}"
        
        prev_map = {get_key(a): a for a in prev_ann}
        curr_map = {get_key(a): a for a in curr_ann}
        
        added = [a for k, a in curr_map.items() if k not in prev_map]
        removed = [a for k, a in prev_map.items() if k not in curr_map]
        persistent = [a for k, a in curr_map.items() if k in prev_map]
        
        return {
            "added_count": len(added),
            "removed_count": len(removed),
            "persistent_count": len(persistent),
            "added_regions": added,
            "removed_regions": removed,
            "persistent_regions": persistent,
            "has_shift": len(added) > 0 or len(removed) > 0
        }

    def _generate_visual_hypothesis(self, evidence_text: str, annotations: list = None) -> Dict[str, Any]:
        """
        CAPA 1 & 4: Structured technical inference from visual evidence.
        Translates visual symptoms and spatial focus to actionable technical targets.
        """
        text = evidence_text.lower()
        annotations = annotations or []
        
        # Default Base
        inference = {
            "description": "Anomalía visual detectada.",
            "layer": "frontend/unknown",
            "component": "unknown",
            "route": None,
            "issue_type": "visual_bug",
            "confidence": "low",
            "suggested_paths": []
        }

        # 1. Semantic Signal Detection
        signals = {
            "responsive": ["frontend/ui", "layout", "frontend/shell/styles", "alignment"],
            "móvil": ["frontend/ui", "layout", "frontend/shell/styles", "alignment"],
            "overlapping": ["frontend/ui", "layout", "frontend/shell/styles", "alignment"],
            "superpuesto": ["frontend/ui", "layout", "frontend/shell/styles", "alignment"],
            "roto": ["frontend/components", "rendering", "frontend/shell/main.js", "logic_error"],
            "error": ["frontend/logic", "data_flow", "backend/core/routing", "runtime_error"],
            "vacío": ["frontend/logic", "data_flow", "backend/core/routing", "empty_state"],
            "menu": ["frontend/shell", "header", "frontend/shell/index.html", "component_failure"],
            "footer": ["frontend/shell", "footer", "frontend/shell/index.html", "component_failure"],
            "dashboard": ["frontend/dashboard", "analytics", "frontend/dashboard/index.html", "component_failure"],
            "auth": ["backend/auth", "security", "backend/auth/logic", "permission_denied"],
            "persistence": ["backend/persistence", "data_access", "backend/db", "write_timeout"],
            "backend": ["backend/core", "api_routing", "backend/engine", "infrastructure_issue"]
        }

        # Priority 1: User Annotations (High Precision Context)
        if annotations:
            comments = " ".join([a.get('comment', '').lower() for a in annotations if a.get('comment')])
            
            # Refine based on annotation comments
            for signal, targets in signals.items():
                if signal in comments:
                    inference.update({
                        "layer": targets[0],
                        "component": targets[1],
                        "route": targets[2],
                        "issue_type": targets[3],
                        "confidence": "high" if len(annotations) > 1 else "medium"
                    })
                    inference["description"] = f"Anomalía localizada en {targets[1]}: {comments or 'Sñalización sin descripción'}"
                    inference["suggested_paths"] = [targets[2]] if targets[2] not in inference["suggested_paths"] else []
                    break
            
            if inference["confidence"] == "low":
                 # Fallback if annotations don't match signals
                 inference.update({
                     "description": f"Foco manual del Creador: {comments or 'Múltiples puntos'}",
                     "confidence": "medium",
                     "layer": "frontend/components"
                 })

        # Priority 2: Text Evidence (Context Enrichment)
        else:
            for signal, targets in signals.items():
                if signal in text:
                    inference.update({
                        "layer": targets[0],
                        "component": targets[1],
                        "route": targets[2],
                        "issue_type": targets[3],
                        "confidence": "medium"
                    })
                    inference["description"] = f"Inferencia por descripción: Posible fallo en {targets[1]}."
                    inference["suggested_paths"] = [targets[2]]
                    break

        # Adjust Roadmap based on inference (Capa 3 logic starts here)
        if inference["suggested_paths"]:
            # We ensure we don't hallucinate non-existent files too much, 
            # but we guide the auditor to these zones.
            inference["roadmap_hint"] = f"Priorizar auditoría en {inference['layer']} / {inference['component']}"

        return inference
