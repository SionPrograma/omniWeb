
import logging
from typing import Dict, Any, List, Optional
from .tracing_api import InteractionTrace

logger = logging.getLogger(__name__)

class SelfCorrectionEngine:
    """
    Diagnoses the trace for anomalies and suggests corrective flags or warnings.
    """
    def diagnose(self, trace: InteractionTrace) -> List[str]:
        diagnostics = []
        
        # 1. Fallback Detection
        if trace.status == "fallback" or (trace.final_response and "no detecté un comando" in trace.final_response.lower()):
            diagnostics.append("FALLBACK_DETECTED: Response suggests command failure or ambiguity.")

        # 2. Intent vs Mode Contradiction
        if trace.detected_intent_group in ["BUILD_INTENT", "REMEDIATION_INTENT"] and trace.response_mode == "natural_chat":
             diagnostics.append("CONTRADICTION: Action intent routed to natural_chat mode.")

        # 3. Missing Memory for Project Scope
        project_keywords = ["roadmap", "bloque", "avance", "proyecto", "status", "arquitectura"]
        if any(kw in trace.user_input.lower() for kw in project_keywords) and trace.memory_refs_count == 0:
             diagnostics.append("MISSING_MEMORY: Project-scoped query but no memory references retrieved.")

        # 4. Inconsistent Tool Selection
        if trace.detected_intent_group == "EXPLORATION_INTENT" and trace.selected_tool == "chat":
             diagnostics.append("TOOL_MISMATCH: Exploration intent but chat tool selected.")

        # 5. Success Check
        if not diagnostics and trace.status == "success":
             diagnostics.append("NOMINAL_EXECUTION: All stages consistent.")

        return diagnostics

self_correction = SelfCorrectionEngine()
