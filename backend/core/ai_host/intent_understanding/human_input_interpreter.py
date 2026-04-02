import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HumanInputInterpreter:
    """
    Interpretation Layer for messy/informal human input.
    Extracts intent, context, signals, and emotional state before cognitive processing.
    """
    
    def interpret(self, text: str) -> Dict[str, Any]:
        msg = text.lower().strip()
        refined_text = self.refine_input(msg)
        
        interpretation = {
            "intent": self._extract_intent(refined_text),
            "context": self._extract_context(refined_text),
            "signals": self._extract_signals(refined_text),
            "clarity": self._assess_clarity(refined_text),
            "user_state": self._detect_user_state(refined_text),
            "original_text": text,
            "refined_text": refined_text
        }
        print(f"DEBUG: [INTERPRETER] Clarity: {interpretation['clarity']} for msg: '{text}'")
        
        logger.info(f"[HUMAN_INTERPRETATION] {interpretation}")
        return interpretation

    def refine_input(self, text: str) -> str:
        """
        Segment and self-correct input based on reformulation markers.
        "Do X, no wait, do Y" -> returns "do Y"
        """
        msg = text.lower().strip()
        
        # Case A: Explicit Reformulation (No, mejor dicho...)
        # Combined markers for both original and new logic
        markers = [
            r"no,\s+mejor\s+dicho", r"no,\s+mejor", r"perd[óo]n,\s+", 
            r"no,\s+wait", r"no,\s+actualmente", r"actually", r"better\s+said",
            r"no,\s+olv[íi]dalo", r"no,\s+mejor\s+decime", r"pero\s+mejor",
            r"en\s+realidad", r"no,\s+espera", r"perdón,\s+quise\s+decir"
        ]
        
        for marker in markers:
            parts = re.split(marker, msg, flags=re.IGNORECASE)
            if len(parts) > 1:
                # We take the last part as the primary correction, 
                # but we scan the discarded part for legacy negative constraints
                discarded = parts[0].strip()
                correction = parts[-1].strip()
                
                # Capture "no me digas", "no repitas", "sin frases", "solo", "mínima", "nada más" etc.
                negations = re.findall(r"(no me digas [^,.]+?|no repitas [^,.]+?|sin [^,.]+?|solo [^,.]+?|mínima [^,.]+?|nada más[^,.]*)", discarded, flags=re.IGNORECASE)
                if negations:
                    combined_negations = ". ".join(negations)
                    logger.info(f"[SELF_CORRECTION] Reformulation detected with constraints. Picked: {combined_negations}. {correction}")
                    return f"{combined_negations}. {correction}"
                
                if len(correction) > 3: # Ensure it's not a tiny fragment
                    logger.info(f"[SELF_CORRECTION] Reformulation detected. Picked: {correction}")
                    return correction
                    
        return text

    def _extract_intent(self, msg: str) -> str:
        # MISSION - Approval / Completion
        if any(w in msg.split() for w in ["aprobado", "listo", "aprobá", "aproba", "perfecto", "looks good", "se ve bien"]):
            return "mission_approval"
            
        # MISSION - Continuity / Flow
        if any(w in msg for w in ["seguí", "segui", "dale", "continuá", "keep", "next", "ahora", "y?", "que mas"]):
            return "mission_followup"
        
        # MISSION - Control / Retries
        if any(w in msg for w in ["reintentá", "reintenta", "abortá", "abortar", "cancelá", "cancelar", "reset", "detener"]):
            return "mission_control"
        
        # MISSION - Adjustment (Constitución Dinámica + Sectorial Freeze + Snapshots)
        if any(w in msg for w in ["ajustá", "ajusta", "corregí", "corregi", "mejorá", "mejora", "quise decir", "ahora", "bloqueá", "bloquea", "permití", "permiti", "sacá", "saca", "volvé", "volve", "congelá", "congela", "freeze", "pausá", "pausa", "descongelá", "descongela", "unfreeze", "restringí", "restringi", "guardá perfil", "guarda perfil", "restaurá perfil", "restaura perfil", "cargá el preset", "carga el preset", "snapshot"]):
            return "mission_adjustment"

        # MISSION - Audit Request
        if any(w in msg for w in ["auditá", "audita", "auditar", "solo auditá", "solo audita", "revisa", "revisá", "inspecciona", "inspeccioná"]):
            return "audit_request"

        # MISSION - Identification (New Mission intent)
        # We look for action verbs but we'll double confirm later with clarity
        if any(w in msg for w in ["implementá", "implementa", "arreglá", "arregla", "creá", "crea", "build", "hacé", "hace", "desarrollá"]):
             return "new_mission_intent"

        # Debug/Fix triggers
        if any(w in msg for w in ["anda", "falla", "raro", "mal", "funciona", "arregla", "bug", "error"]):
            return "debug"
        # Creation triggers
        if any(w in msg for w in ["crea", "hace", "build", "pon", "agregá", "implementa", "nueva"]):
            return "create"
        # Decision triggers
        if any(w in msg for w in ["decidi", "decidí", "elegí", "elige", "elegir", "cuál", "prioriza", "qué hago", "choice", "choose"]):
            return "decide"
        # Exploration/Question
        if any(w in msg for w in ["qué onda", "fijate", "mirá", "qué es"]):
            return "explore"
        
        # Clarification triggers
        if any(w in msg for w in ["explicá", "explica", "entendi", "entendí", "cómo así", "como asi", "qué es esto", "que es esto", "o sea", "osea"]):
            return "clarification"
        
        return "neutral_query"

    def _extract_context(self, msg: str) -> str:
        # References (Eso, este, ese)
        if any(w in msg.split() for w in ["eso", "ese", "esa", "esto", "este", "esta", "ello"]):
            return "referential_context"
        
        if any(w in msg for w in ["chat", "habla", "responde", "dijo"]):
            return "conversational_behavior"
        if any(w in msg for w in ["ui", "visual", "pantalla", "botón", "color"]):
            return "interface_design"
        if any(w in msg for w in ["núcleo", "backend", "procesamiento", "lento", "cpu"]):
            return "core_system"
        if any(w in msg for w in ["memoria", "recordas", "dije antes"]):
            return "session_persistence"
        
        return "general_system"

    def _extract_signals(self, msg: str) -> List[str]:
        # Extract meaningful nouns or concepts + operational signals
        signals = []
        
        # Operational Mode Signals
        if any(w in msg for w in ["conservador", "prudente", "despacio", "con cuidado", "sin romper"]):
             signals.append("conservative_mode")
        if any(w in msg for w in ["auditá primero", "solo auditá", "revisá primero", "inspeccioná", "audit_only"]):
             signals.append("audit_only")
        if any(w in msg for w in ["roadmap", "antes del plan", "primero el plan", "ver pasos"]):
             signals.append("roadmap_first")
        if any(w in msg for w in ["sin romper", "no rompas", "sin afectar"]):
             signals.append("has_constraints")
             
        key_terms = [
            "chat", "tono", "bug", "mobile", "interfaz", "log", "latency", "tarda",
            "lento", "latencia", "video", "responde", "vínculo", "link",
            "velocidad", "natural", "robot", "creador", "omni", "estilo",
            "ux", "ui", "arquitectura", "backend", "frontend", "lógica", "logic",
            "base", "núcleo", "core", "estado", "state", "buffer", "memoria",
            "mem", "cpu", "performance", "rendimiento", "estabilidad",
            "swarm", "agentes", "shadow", "auth", "login", "permisos", "database"
        ]
        for term in key_terms:
            if term in msg:
                signals.append(term)
        return list(set(signals)) # Deduplicate

    def _assess_clarity(self, msg: str) -> str:
        import unicodedata
        def normalize(s):
            return "".join(c for c in unicodedata.normalize('NFD', s.lower()))
            
        words = msg.split()
        msg_norm = normalize(msg)
        
        # Follow-up / Clarification markers (Continuity)
        followup_bullets = ["seguí", "segui", "dale", "y ahora", "and now", "seguimos", "keep going", "continuemos", "go on", "continuar", "explicá", "explica", "cómo así", "como asi", "entendi", "entendí"]
        if any(normalize(f) in msg_norm for f in followup_bullets):
             return "follow_up"
        
        # Vague References (Eso, lo otro)
        references = ["lo otro", "eso", "aquello", "ese", "esa", "este", "esta", "ahí", "ahi", "allá", "alla", "acá", "aca"]
        if any(normalize(r) == normalize(word) for r in references for word in words) or re.search(r"\w+(lo|la|los|las|lo|la)$", msg_norm):
             return "vague"

        if len(words) < 3 and not any(normalize(f) in msg_norm for f in followup_bullets):
            return "ambiguous"
        
        if any(normalize(w) in msg_norm for w in ["algo", "onda", "medio", "tipo", "coso"]):
            return "partial"
        return "clear"

    def _detect_user_state(self, msg: str) -> str:
        if any(w in msg for w in ["mierda", "malísimo", "no anda", "harto", "che", "anda mal"]):
            return "frustrated"
        if any(w in msg for w in ["cómo", "por qué", "qué es esto", "perdido", "qué pasa", "no sé", "no se", "distinto"]):
            return "confused"
        if any(w in msg for w in ["mirá", "probá", "chequeá", "dale", "fijate"]):
            return "exploratory"
        return "neutral"

human_interpreter = HumanInputInterpreter()
