import logging
import random
import re
from typing import Dict, Any, Optional, List
from .output_policy import get_output_policy

# Structured imports for type hinting
from ..reasoning.runtime_truth import StructuredDiagnosis
from ..planner.task_planner import TaskPlan
from ..reasoning.verification_layer import VerificationResult

logger = logging.getLogger(__name__)


class ExecutiveSynthesis:
    """
    Unified Synthesis Engine for OmniWeb.
    Transforms memory fragments into executive, reasoned responses.
    Prevents memory dumps and raw template vocalization.
    Requirement: single useful conclusion, no 'None' values.
    """

    def _humanize_path(self, path: str) -> str:
        if not path: return ""
        path = path.replace("\\", "/")
        parts = path.split("/")
        if len(parts) > 1:
            filename = parts[-1]
            name = filename.split(".")[0].replace("_", " ")
            return f"el módulo {name} ({filename}) en {parts[0]}"
        return path.replace("_", " ")

    def synthesize(self, 
                   working: Dict[str, Any], 
                   project: Dict[str, Any], 
                   query: str, 
                   lang: str = "es",
                   tone: Optional[str] = None,
                   surface: str = "chat") -> str:
        
        policy = get_output_policy(query, surface=surface)
        is_natural = tone == "natural_chatbot" or policy.tone == "natural"
        # 1. Null-handling & Defaults (OS-like resilience)
        last_op = working.get("last_operation_summary")
        last_file = working.get("last_important_file")
        block = project.get("roadmap_block", "Bloque 5")
        fixes = project.get("validated_fixes", [])
        rules = project.get("hard_rules", [])
        sensitive = project.get("sensitive_modules", [])
        deferred = project.get("deferred_items", [])

        # 2. Executive Reasoning Logic (Synthesis Layer)
        low_query = query.lower()
        
        # 3. Signals & Intents
        is_entity_mention = any(re.search(rf"\b{k}\b", low_query) for k in ["archivo", "módulo", "modulo"])
        is_fixes = any(re.search(rf"\b{k}\b", low_query) for k in ["fix", "cerrado", "arregla", "redundante", "reabrir", "closed", "validados", "cerrada"])
        is_impact = any(re.search(rf"\b{k}\b", low_query) for k in ["sensible", "tocar", "peligro", "riesgo", "comprometido", "delicada", "arriesgado"])
        is_minimal = policy.is_minimal
        is_forbidden_gen = any(k in low_query for k in ["frase genérica", "frases genéricas", "no reemplaces", "sin rellenar"])
        
        # Positive specific requests (Whitelist for Minimal Mode)
        positive_discovery = any(k in low_query for k in ["qué estábamos haciendo", "qué hicimos", "en qué andábamos", "qué veníamos haciendo", "que estabamos haciendo", "qué estamos cerrando", "qué queda por cerrar", "qué veníamos cerrando", "recordame qué", "recordame que", "antes de seguir", "hilo", "lo último", "lo ultimo", "delicado"])
        positive_roadmap = any(k in low_query for k in ["qué bloque", "en qué bloque", "dime el bloque", "decime el bloque", "cuál bloque", "roadmap", "plan"])
        
        # Determine if we should treat this as discovery/roadmap even if not specific whitelist (for normal mode)
        is_discovery = positive_discovery or (not is_minimal and any(k in low_query for k in ["haciendo", "andábamos", "hicimos", "cerrando", "terminando", "ajustar", "moviendo"]))
        is_roadmap = positive_roadmap or (not is_minimal and any(k in low_query for k in ["bloque", "roadmap", "plan"]))

        # 4. HARD SUPPRESSION (Decision Gate via OutputPolicy)
        
        # Rule: In minimal mode, hide Sections A and B unless they are explicitly whitelisted.
        # Enforcement: Specific requests for 'vigente' or 'archivo' bypass general dump/report suppression.
        is_explicit_request = any(k in low_query for k in ["vigente", "archivo", "cerrada", "diferida", "sensible"])
        
        hide_working = (is_minimal and not positive_discovery) or (not is_explicit_request and policy.suppress_runtime)
        hide_block = (is_minimal and not positive_roadmap) or (not is_explicit_request and policy.suppress_block)
        
        should_omit = any(k in low_query for k in ["omitila", "omite", "omití"])
        is_concrete = any(k in low_query for k in ["vigencia concreta", "exactamente qué", "exactamente que", "dime exactamente", "decime exactamente", "decime solo", "en una sola respuesta"]) or policy.is_minimal

        msg_parts = []

        # A. Continuity & Vigency (Working Memory)
        continuity_msg = ""
        # Enforcement: hard hide if minimal and not explicitly whitelisted
        if not hide_working and (is_discovery or is_concrete or "vigente" in low_query or "último archivo" in low_query):
            if last_op and last_file:
                if lang == "es":
                    continuity_msg = f"Sigue vigente la **{last_op}** en el archivo `{last_file}`."
                else:
                    continuity_msg = f"The **{last_op}** is still current, specifically on `{last_file}`."
            else:
                if not should_omit and (is_discovery or is_concrete or "vigente" in low_query or "último archivo" in low_query):
                    if lang == "es":
                        parts = []
                        # Focus on concrete current goal if no last_op exists
                        if is_discovery or "vigente" in low_query:
                            parts.append("Actualmente seguimos cerrando la capa de memoria, síntesis y verbalización para asegurar la estabilidad del sistema.")
                        if "último archivo" in low_query and not last_file:
                            parts.append("No tengo registro del último archivo real procesado.")
                        
                        if not parts:
                            if is_forbidden_gen or is_concrete:
                                continuity_msg = "No hay una tarea operativa específica en registro inmediato,"
                            else:
                                continuity_msg = "No tengo registro del último archivo, pero mantengo la vinculación con el flujo actual."
                        else:
                            continuity_msg = " ".join(parts)
                    else:
                        parts = []
                        if "curr" in low_query or "active" in low_query or "vigen" in low_query:
                            parts.append("Currently, the focus remains on the stabilization of the memory, synthesis, and verbalization layer.")
                        if "last file" in low_query and not last_file:
                            parts.append("I don't have a record of the last real file processed.")
                        
                        if not parts:
                            if is_forbidden_gen or is_concrete:
                                continuity_msg = "No specific task in storage right now,"
                            else:
                                continuity_msg = "I don't have a record of the last file, but I'm keeping the link to the current flow."
                        else:
                            continuity_msg = " ".join(parts)
        
        if continuity_msg: msg_parts.append(continuity_msg)

        # B. Context & Roadmap (Project Memory)
        # Enforcement: hide block unless the user is specifically interested in the roadmap/plan.
        if not hide_block and (is_roadmap or is_concrete or "en qué bloque" in low_query):
            status = "activo" if lang == "es" else "active"
            if lang == "es":
                text = f"Esta labor pertenece al **{block}** ({status})"
                if "reporte" in low_query or is_concrete:
                    text = f"El trabajo actual se enmarca en el **{block}** ({status})."
                msg_parts.append(text)
            else:
                text = f"This work belongs to **{block}** ({status})"
                if "report" in low_query or is_concrete:
                    text = f"Current work is framed within **{block}** ({status})."
                msg_parts.append(text)

        # C. Proactive Redundancy Check (Validated Fixes Reasoning)
        if (is_fixes or is_concrete) and not is_minimal and not policy.is_brief:
            already_fixed = None
            if fixes:
                forbidden_keywords = ["limpio", "sistema", "módulo", "archivo", "nuevo", "actual"]
                for fix in fixes:
                    fix_words = [w for w in fix.lower().split() if len(w) > 5 and w not in forbidden_keywords]
                    if any(word in query.lower() for word in fix_words):
                        already_fixed = fix
                        break
                
                if already_fixed:
                    if lang == "es":
                        msg_parts.append(f"Reabrir temas sobre `{already_fixed}` sería **redundante**, ya que ese fix fue validado y cerrado previamente.")
                    else:
                        msg_parts.append(f"Reopening topics about `{already_fixed}` would be **redundant** as that fix was previously validated and closed.")
                elif is_fixes or is_concrete:
                    formatted_fixes = ", ".join([f"`{f}`" for f in fixes])
                    if lang == "es":
                        msg_parts.append(f"Quedaron cerradas y validadas las siguientes partes: {formatted_fixes}.")
                    else:
                        msg_parts.append(f"The following parts were closed and validated: {formatted_fixes}.")

        # D. Roadmap & Deferred Items (Project Memory)
        if deferred and (is_concrete or any(k in query.lower() for k in ["diferid", "pospue", "later", "deferred"])) and not is_minimal:
            item = deferred[0]
            if lang == "es":
                msg_parts.append(f"En cuanto a lo pendiente, `{item}` quedó **diferido** para más adelante.")
            else:
                msg_parts.append(f"As for pending items, `{item}` was **deferred** for later.")

        # E. Impact Warning (Sensitive Modules)
        if is_impact or (is_entity_mention and "sensible" in low_query) or is_concrete:
            if sensitive:
                target_sens = sensitive[0]
                for s in sensitive:
                    if s.split('/')[-1] in query.lower():
                        target_sens = s
                        break
                
                human_sens = self._humanize_path(target_sens)
                if lang == "es":
                    msg_parts.append(f"El módulo sensible que no conviene tocar ahora es **{human_sens}**, para mantener la estabilidad base.")
                else:
                    msg_parts.append(f"The sensitive module to avoid touching for now is **{human_sens}**, to maintain base stability.")

        # F. Final Executive Polish
        if not msg_parts:
            if should_omit or is_minimal: return ""
            if lang == "es":
                return "Acá estoy. ¿En qué puedo asistirte con el flujo actual?" if is_natural else "Sistema nominal. Aguardando instrucción para el flujo seleccionado."
            else:
                return "I'm here. How can I assist you with the current flow?" if is_natural else "System nominal. Awaiting instruction for the selected flow."

        final_msg = " ".join(msg_parts)
        if is_natural:
            final_msg = final_msg.replace("**", "").replace("`", "")
            if lang == "es":
                final_msg = final_msg.replace("Sigue vigente la ", "Seguimos con la ").replace("Esta labor pertenece al ", "Estamos en el ")
            else:
                final_msg = final_msg.replace("The ", "").replace(" is still current", " is what we're on")
        
        return final_msg

    def synthesize_analysis(self, 
                            diagnosis: StructuredDiagnosis, 
                            plan: TaskPlan, 
                            verification: VerificationResult, 
                            execution_result: Dict[str, Any],
                            chip_report: str = "",
                            lang: str = "es",
                            query: str = "",
                            surface: str = "chat") -> str:
        """
        Grounded synthesis of technical logic.
        Communicates Diagnosis, Planning, and Verification state clearly.
        """
        policy = get_output_policy(query, surface=surface)
        is_es = lang == "es"
        
        # 1. DIAGNOSIS BLOCK
        if diagnosis:
            diag_title = "**ANÁLISIS DE RUNTIME (L1/L2)**" if is_es else "**RUNTIME ANALYSIS (L1/L2)**"
            diag_status = f"Estado: `{diagnosis.diagnosis_type.upper()}` (Confianza: {int(diagnosis.confidence_score * 100)}%)"
            
            anomalies_list = []
            for a in diagnosis.detected_anomalies:
                anomalies_list.append(f"- `{a['type'].upper()}` detectado en `{a['source']}`: {a['value']}")
            
            anomalies_body = "\n".join(anomalies_list) if anomalies_list else ("- Parámetros nominales." if is_es else "- Nominal parameters.")
            diagnosis_section = f"{diag_title}\n{diag_status}\n{anomalies_body}"
        else:
            diagnosis_section = ""

        # 2. OPERATIVE PLAN BLOCK
        plan_title = f"**PLAN OPERATIVO: {plan.goal}**"
        task_lines = []
        for t in plan.tasks:
            # Determine icon based on execution state
            icon = "⚪" # Pending
            if t.id in execution_result.get("steps_completed", []):
                icon = "✅"
            elif execution_result["status"] == "WAITING_CONFIRMATION" and t.id == execution_result.get("current_step"):
                icon = "⚠"
            elif execution_result["status"] == "BLOCKED":
                icon = "🚫"
            elif execution_result["status"] == "RUNNING":
                icon = "⚙️"
            
            task_lines.append(f"{icon} {t.id}. {t.description}")
        
        plan_body = "\n".join(task_lines)
        plan_section = f"{plan_title}\n{plan_body}"

        # 3. VERIFICATION & SECURITY BLOCK
        if verification:
            verif_title = "**AUDITORÍA DE SEGURIDAD (VERIFICATION LAYER)**" if is_es else "**SECURITY AUDIT (VERIFICATION LAYER)**"
            verif_status = f"Resultado: `{verification.verification_mode.upper()}`"
        
            verif_notes = []
            if verification.global_notes:
                for n in verification.global_notes:
                    verif_notes.append(f"- {n}")
            
            # Cross-reference individual task rejections
            for tv in verification.task_verifications:
                if not tv.is_valid:
                    verif_notes.append(f"- Tarea {tv.task_id} RECHAZADA: {tv.reject_reason}")

            verif_body = "\n".join(verif_notes) if verif_notes else ("- Plan validado sin conflictos." if is_es else "- Plan validated without conflicts.")
            verif_section = f"{verif_title}\n{verif_status}\n{verif_body}"
        else:
            verif_section = ""

        # 4. CHIP ECOSYSTEM STATUS
        chip_section = f"**ESTADO DE MÓDULOS (CHIPS)**\n{chip_report}" if chip_report else ""

        # 5. EXECUTIVE CONCLUSION
        conclusion_title = "**CONCLUSIÓN EJECUTIVA**" if is_es else "**EXECUTIVE CONCLUSION**"
        
        mode = verification.verification_mode if verification else "nominal"
        if mode == "blocked":
            conclusion = "Se ha bloqueado la ejecución por inconsistencia de datos o target inexistente." if is_es else "Execution blocked due to data inconsistency or missing target."
        elif mode == "clarification":
            conclusion = "Se requiere aclaración del usuario para resolver ambigüedad entre intención y telemetría." if is_es else "User clarification required to resolve ambiguity between intent and telemetry."
        elif mode == "approval_required":
            conclusion = "Plan verificado. Esperando aprobación manual para ejecutar acciones peligrosas." if is_es else "Plan verified. Awaiting manual approval for dangerous actions."
        elif mode == "nominal":
            conclusion = "Continuando con la ejecución de los pasos pendientes de la misión." if is_es else "Continuing with the execution of the pending mission steps."
        else:
            conclusion = "Plan verificado y ejecución segura iniciada exitosamente." if is_es else "Plan verified and safe execution started successfully."

        # Combine Final Response (SOLO VOZ OFICIAL LIMPIA POR DEFECTO)
        
        # Determine if we should show the full breakdown
        # Show breakdown only if explicitly requested or in high-confidence executive mode
        show_breakdown = (not policy.is_minimal and not policy.suppress_runtime and policy.is_report_mode and 
                          any(k in query.lower() for k in ["reporte", "detalle", "análisis", "analisis", "pasos", "plan", "por qué", "por que"]))

        if not show_breakdown:
             # VOICE CLEANUP: Solo conclusión + Misión si aplica
             final_msg = conclusion
             
             # Append brief mission status if open (SILENT DIRECTOR: Only if relevant to query)
             try:
                 # SILENT DIRECTOR: Solo inyectamos estado de misión si parece una consulta operativa real
                 # Usamos palabras completas para evitar falsos positivos (como 'que' dentro de otras palabras)
                 work_keywords = [r"\bseguí\b", r"\bdale\b", r"\bqué\b", r"\bhaciendo\b", r"\bplan\b", r"\bmisión\b", r"\bmision\b", r"\bestado\b", r"\bwork\b", r"\bmission\b"]
                 is_work_related = any(re.search(kw, query.lower()) for kw in work_keywords)
                 if is_work_related:
                      from ..memory.mission_manager import mission_manager
                      mission = mission_manager.get_active_mission()
                      if mission:
                          status_icon = "⚙️" if mission.status.value == "OPEN" else "⏸️"
                          final_msg += f"\n\n{status_icon} **MISIÓN ACTIVA:** {mission.active_goal} ({len(mission.completed_steps)}/{len(mission.completed_steps) + len(mission.pending_steps)} pasos)"
             except:
                 pass
             
             return final_msg

        # Full Technical Report (Executive Mode - Only when requested)
        response_parts = [diagnosis_section, plan_section, verif_section]
        
        # 6. MISSION CONTINUITY (Persistence Anchor)
        try:
             from ..memory.mission_manager import mission_manager
             mission = mission_manager.get_active_mission()
             if mission:
                 mission_title = "**ESTADO DE MISIÓN (PERSISTENTE)**" if is_es else "**MISSION STATUS (PERSISTENT)**"
                 mission_info = (
                     f"- Objetivo: {mission.active_goal}\n"
                     f"- Estado: `{mission.status.value}`\n"
                     f"- Sincronización: Activa en `database`"
                 ) if is_es else (
                     f"- Goal: {mission.active_goal}\n"
                     f"- Status: `{mission.status.value}`\n"
                     f"- Sync: Active in `database`"
                 )
                 response_parts.append(f"{mission_title}\n{mission_info}")
        except Exception as e:
             logger.warning(f"[SYNTHESIS] Could not append mission info: {e}")

        if chip_section: response_parts.append(chip_section)
        response_parts.append(conclusion_section)

        return "\n\n".join(response_parts)

executive_synthesis = ExecutiveSynthesis()

