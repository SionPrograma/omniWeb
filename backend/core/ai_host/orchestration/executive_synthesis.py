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
        # Unified keywords with intent patterns (L120-132) to prevent partial synthesis
        is_continuity = any(k in query.lower() for k in ["haciendo", "andábamos", "andabamos", "historial", "hicimos", "doing", "was doing", "archivo", "módulo", "modulo"])
        is_roadmap = any(k in query.lower() for k in ["bloque", "roadmap", "plan", "sigue", "next", "vigent", "pertenece"])
        is_fixes = any(k in query.lower() for k in ["fix", "cerrado", "arregla", "redundante", "reabrir", "closed", "validados"])
        is_impact = any(k in query.lower() for k in ["sensible", "tocar", "peligro", "riesgo", "comprometido", "delicada"])

        msg_parts = []

        # A. Continuity & Vigency (Working Memory)
        continuity_msg = ""
        if is_continuity or not (is_roadmap or is_fixes or is_impact):
            if last_op and last_file:
                if lang == "es":
                    continuity_msg = f"Sigue vigente la **{last_op}** en el archivo `{last_file}`."
                else:
                    continuity_msg = f"The **{last_op}** is still current, specifically on `{last_file}`."
            else:
                # INTEGRATED NO-DATA: subordinate clause instead of leading dominance
                if is_continuity:
                    if lang == "es":
                        continuity_msg = "No tengo registro del último archivo, pero mantengo la vinculación con el flujo actual."
                    else:
                        continuity_msg = "I don't have a record of the last file, but I'm keeping the link to the current flow."
        
        if continuity_msg: msg_parts.append(continuity_msg)

        # B. Context & Roadmap (Project Memory)
        if is_roadmap or (is_continuity and not last_op):
            status = "activo" if lang == "es" else "active"
            if lang == "es":
                msg_parts.append(f"Esta labor pertenece al **{block}** ({status}) y es coherente con las reglas del roadmap actual.")
            else:
                msg_parts.append(f"This work belongs to **{block}** ({status}) and is consistent with the current roadmap rules.")

        # C. Proactive Redundancy Check (Validated Fixes Reasoning)
        if is_fixes or is_continuity:
            # Proactive check: avoid common adjectives false positives by using tighter word matching or length check
            already_fixed = None
            if fixes:
                # Avoid matching common words like "limpio", "módulo", "sistema"
                forbidden_keywords = ["limpio", "sistema", "módulo", "archivo", "nuevo", "actual"]
                for fix in fixes:
                    fix_words = [w for w in fix.lower().split() if len(w) > 5 and w not in forbidden_keywords]
                    if any(word in query.lower() for word in fix_words):
                        already_fixed = fix
                        break
                
                if already_fixed:
                    if lang == "es":
                        msg_parts.append(f"Ojo: reabrir temas sobre `{already_fixed}` sería **redundante**, ya que ese fix fue validado y cerrado previamente.")
                    else:
                        msg_parts.append(f"Be careful: reopening topics about `{already_fixed}` would be **redundant** as that fix was previously validated and closed.")
                elif is_fixes:
                    # General fix status
                    if lang == "es":
                        msg_parts.append(f"Hemos validado {len(fixes)} fixes en este bloque.")
                    else:
                        msg_parts.append(f"We have validated {len(fixes)} fixes in this block.")

        # D. Roadmap & Deferred Items (Project Memory)
        if deferred and any(k in query.lower() for k in ["diferid", "pospue", "later", "deferred"]):
            # Specifically alert about deferred items if asked or if roza
            item = deferred[0]
            if lang == "es":
                msg_parts.append(f"Ojo: nota que `{item}` quedó **diferido** para más adelante según el roadmap.")
            else:
                msg_parts.append(f"Note: `{item}` was **deferred** for later in the roadmap.")

        # D. Impact Warning (Sensitive Modules)
        if is_impact or is_continuity:
            if sensitive:
                # Find if query mentions a sensitive module
                target_sens = sensitive[0]
                for s in sensitive:
                    if s.split('/')[-1] in query.lower():
                        target_sens = s
                        break
                
                if lang == "es":
                    msg_parts.append(f"Como advertencia de impacto, evitá tocar `{target_sens}` aún, para no comprometer la estabilidad base.")
                else:
                    msg_parts.append(f"Impact warning: avoid touching `{target_sens}` for now to maintain stability.")

        # E. Final Executive Polish
        if not msg_parts:
            if lang == "es":
                return "Sistema nominal. Todos los procesos están sincronizados dentro del roadmap del Bloque actual. ¿En qué puedo ayudarte hoy?"
            else:
                return "System nominal. All processes are synchronized within the current Block roadmap. How can I help you today?"

        return " ".join(msg_parts)

executive_synthesis = ExecutiveSynthesis()
