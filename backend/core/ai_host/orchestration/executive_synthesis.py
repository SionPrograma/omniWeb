import logging
import random
import re
from typing import Dict, Any, Optional

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
                   lang: str = "es") -> str:
        
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
        is_minimal = any(k in low_query for k in ["solo", "only", "nada más", "nada mas", "frase corta", "una frase", "únicamente", "unicamente", "mínima", "minima", "sin agregar"])
        is_forbidden_gen = any(k in low_query for k in ["frase genérica", "frases genéricas", "no reemplaces", "sin rellenar"])
        
        # Positive specific requests (Whitelist for Minimal Mode)
        positive_discovery = any(k in low_query for k in ["qué estábamos haciendo", "qué hicimos", "en qué andábamos", "qué veníamos haciendo", "que estabamos haciendo"])
        positive_roadmap = any(k in low_query for k in ["qué bloque", "en qué bloque", "dime el bloque", "decime el bloque", "cuál bloque", "roadmap", "plan"])
        
        # Determine if we should treat this as discovery/roadmap even if not specific whitelist (for normal mode)
        is_discovery = positive_discovery or (not is_minimal and any(k in low_query for k in ["haciendo", "andábamos", "hicimos"]))
        is_roadmap = positive_roadmap or (not is_minimal and any(k in low_query for k in ["bloque", "roadmap", "plan"]))

        # 4. HARD SUPPRESSION (Decision Gate)
        negation_markers = ["no me digas", "no menciones", "no repitas", "no agregues", "no incluyas", "sin decir", "sin leer", "sin mencionar", "sin incluir", "omite", "omití", "no me hagas", "no cambies", "sin reporte", "no reportes", "no reporte", "sin dump"]
        
        # Rule: In minimal mode, hide Sections A and B unless they are explicitly whitelisted.
        # Enforcement: Specific requests for 'vigente' or 'archivo' bypass general dump/report suppression.
        is_explicit_request = any(k in low_query for k in ["vigente", "archivo", "cerrada", "diferida", "sensible"])
        
        hide_working = (is_minimal and not positive_discovery) or (not is_explicit_request and any(n in low_query for n in negation_markers) and ("haciendo" in low_query or "working" in low_query or "memoria" in low_query or "dump" in low_query))
        hide_block = (is_minimal and not positive_roadmap) or (not is_explicit_request and any(n in low_query for n in negation_markers) and ("bloque" in low_query or "roadmap" in low_query or "reporte" in low_query))
        
        should_omit = any(k in low_query for k in ["omitila", "omite", "omití"])
        is_concrete = any(k in low_query for k in ["vigencia concreta", "exactamente qué", "exactamente que", "dime exactamente", "decime exactamente", "decime solo", "en una sola respuesta"])

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
                        if "vigente" in low_query:
                            parts.append("Actualmente sigue vigente el cierre y estabilización de la capa de memoria, síntesis y verbalización.")
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
        # Enforcement: hard hide if minimal and not explicitly whitelisted
        if not hide_block and (is_roadmap or (is_discovery and not last_op) or is_concrete):
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
        if (is_fixes or is_concrete) and not is_minimal:
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
                return "Sistema nominal. Todo coordinado dentro del Bloque actual. ¿Cómo procedemos?"
            else:
                return "System nominal. Everything coordinated within the current Block. How shall we proceed?"

        return " ".join(msg_parts)

executive_synthesis = ExecutiveSynthesis()
