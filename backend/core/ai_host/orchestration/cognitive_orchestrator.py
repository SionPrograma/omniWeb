import logging
from typing import Dict, Any, Optional
from backend.core.ai_host.processors.base import AICommandResponse
from backend.core.system_state.engine import state_engine
from backend.core.omni_runtime.runtime_controller import runtime_controller
from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.memory.semantic_memory import semantic_memory

logger = logging.getLogger(__name__)

class CognitiveOrchestrator:
    """
    Cognitive Orchestration Layer (Additive / Non-Destructive)
    Connects:
    1. Deliberation Layer (BrainRouter)
    2. System State & Chips Awareness
    3. Memory & Logbook Context
    4. Response Normalization (Natural Language)
    """
    
    def __init__(self, command_router=None):
        from backend.core.ai_host.routing.command_router import ai_command_router
        self.command_router = command_router or ai_command_router
        self.brain = BrainRouter(self.command_router)
        
    async def orchestrate(
        self, 
        message: str, 
        understanding: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None,
        raw_response: Optional[AICommandResponse] = None
    ) -> AICommandResponse:
        
        session_id = str(context.get("user_id", "default_user")) if context else "default_user"
        
        logger.info(f"[ORCHESTRATOR] Processing Response Pipeline | Intent: {understanding.get('intent_group', 'unknown')}")

        # 1. State & Chip Awareness Integration
        system_state = await state_engine.get_state()
        runtime_ctx = runtime_controller.state
        
        # 2. Context Integration (Recent conversation via semantic memory)
        recent_context = []
        try:
            recent_interactions = semantic_memory.get_recent_interactions(session_id, limit=3)
            recent_context = [f"User: {m.get('prompt', '')} | Omni: {m.get('response', '')}" for m in recent_interactions]
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Memory integration warning: {e}")
            
        enhanced_understanding = dict(understanding)
        enhanced_understanding["recent_conversation"] = recent_context
        
        # 3. Deliberation Output (Connect to Brain or use Raw)
        if raw_response:
            brain_response = raw_response
        else:
            try:
                brain_response = await self.brain.process(
                    message=message,
                    context=context,
                    runtime_context=runtime_ctx,
                    chip_registry=self.command_router.registry,
                    system_state=system_state,
                    understanding=enhanced_understanding
                )
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Brain Deliberation Failed: {e}")
                brain_response = None
            
        # 3.1 Messaging Priority Fallback
        if not brain_response or (not raw_response and brain_response.intent == "chat"):
            comm_proc = self.command_router.registry.get_processor("communication")
            if comm_proc and await comm_proc.can_handle(message):
                try:
                    res = await comm_proc.process(message, context=context)
                    if res: brain_response = res
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Messaging processor error: {e}")

        # 3.2 Other Processors Fallback
        if not brain_response or brain_response.intent == "chat":
            for name, proc in self.command_router.registry._processors.items():
                if name in ["communication", "chat"]: continue 
                try:
                    if await proc.can_handle(message):
                        res = await proc.process(message, context=context)
                        if res: 
                            brain_response = res
                            break
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Processor '{name}' error: {e}")

        # 4. Fallback Prevention
        if not brain_response:
            chat_proc = self.command_router.registry.get_processor("chat")
            if chat_proc:
                brain_response = await chat_proc.process(message, context=context)
            
            if not brain_response:
                brain_response = AICommandResponse(
                    intent="orchestrator_fallback", 
                    status="success", 
                    message="hmm… algo no terminó de tomar forma ahí" if system_state.health.value != "healthy" else "no me termina de cerrar lo que salió recién"
                )

        # 5. Cognitive Unification: Weave context + state + mode into the response
        brain_response.message = self._unify_response(
            text=brain_response.message,
            system_state=system_state,
            mode=understanding.get("mode", "direct_response"),
            recent_context=recent_context,
            intent_group=understanding.get("intent_group", "CONVERSATIONAL_INTENT")
        )
        
        # 6. Final Adaptation (Antimodal & Telemetry Integration)
        from backend.core.antimodal.antimodal_controller import antimodal_controller
        brain_response.message = antimodal_controller.process_ai_response(brain_response.message)
        
        # Log telemetry before returning
        try:
            from backend.core.usage.usage_tracker import usage_tracker
            usage_tracker.log_event(
                event_type="orchestrated_response",
                chip_slug="ai-host",
                metadata={
                    "intent": brain_response.intent,
                    "status": brain_response.status,
                    "mode": understanding.get("mode"),
                    "health": system_state.health.value if hasattr(system_state, 'health') else "unknown"
                }
            )
        except: pass
        
        return brain_response

    FORBIDDEN_LABELS = [
        "OBSERVATION", "OBSERVACIÓN", "ANALYSIS", "ANÁLISIS", "PLAN", "MISSION", "MISIÓN",
        "HYPOTHESIS PRIMARIA", "HIPÓTESIS PRIMARIA", "HYPOTHESIS", "HIPÓTESIS",
        "ALTERNATIVE EXPLANATION", "EXPLICACIÓN ALTERNATIVA", "EVIDENCE", "EVIDENCIA",
        "CONFIDENCE LEVEL", "NIVEL DE CONFIANZA", "MISSING EVIDENCE", "EVIDENCIA FALTANTE",
        "RECOMMENDED ACTION", "ACCIÓN RECOMENDADA", "RECOMMENDED NEXT STEP",
        "RELIABILITY", "CONFIABILIDAD", "LEARNING", "APRENDIZAJE", "PATCH", "PARCHE", 
        "CONTEXTO COGNITIVO", "TECHNICAL REASONING", "SYSTEM STATUS", "PRIMARIA", "SECUNDARIA",
        "TO", "FROM", "ORIGINAL", "TRANSLATED", "CONFIRMATION", "YOUR CONTACTS", "CONTACTS",
        "MESSAGE", "ORIGINAL TEXT", "TARGET LANGUAGE", "STATUS", "RECIPIENT",
        "INFORME DE SALUD", "SALUD DEL SISTEMA", "SOLUCIONES DE AUTOCURACIÓN", "ACCIONES DE AUTOCURACIÓN",
        "CONFIRMACIÓN DE AUTOCURACIÓN", "AUTOCURACIÓN COMPLETADA", "REPARACIÓN", "SOLUCIÓN DISPONIBLE",
        "HEALTH REPORT", "SYSTEM HEALTH", "SELF-HEALING SOLUTIONS", "HEALING ACTIONS",
        "CONFIRMATION REQUIRED", "HEALING COMPLETED", "REPAIR", "SOLUTION AVAILABLE",
        "REPORTE DE DIAGNÓSTICO TÉCNICO", "TECHNICAL DIAGNOSTIC REPORT", "REPORTE DE DIAGNÓSTICO",
        "DIAGNOSTIC REPORT", "PATCH PREVIEW", "VISTA PREVIA DEL PARCHE", "PATCH GENERATED",
        "MISSION CONTROL", "COMANDO RECIBIDO", "COMMAND RECEIVED", "SYSTEM REQUEST", "EXECUTION STATUS", "ESTADO DE EJECUCIÓN",
        "PLAN INTEGRADO", "INTEGRATED PLAN", "VERIFICACIÓN", "VERIFY", "RESULTADO", "OUTCOME", "MISIÓN DISPUESTA", "MISSION DISPATCHED"
    ]

    def _unify_response(self, text: str, system_state: Any, mode: str, recent_context: list, intent_group: str) -> str:
        """
        Cognitive Response Transformation Layer.
        Converts structured 'thoughts' into a single natural voice.
        """
        logger.info("UNIFY_LAYER_EXECUTED")
        if not text:
            import random
            from backend.core.ai_host.sessions import session_state
            lang = session_state.language
            fallbacks = [
                "hmm… algo no terminó de tomar forma ahí", 
                "no me termina de cerrar lo que salió recién"
            ] if lang == "es" else [
                "hmm… something didn't quite take shape there", 
                "not quite sure about how that turned out"
            ]
            text = random.choice(fallbacks)

        health = "healthy"
        try:
            health = system_state.health.value if hasattr(system_state, 'health') else "healthy"
        except: pass
        
        # --- Context Continuity ---
        context_hint = ""
        if recent_context:
            last_interaction = recent_context[-1]
            if isinstance(last_interaction, str) and "User:" in last_interaction:
                try:
                    # Capture the essence of the last prompt
                    context_hint = last_interaction.split("User:")[1].split("|")[0].strip()
                except: pass

        # Detect User Language Preference
        from backend.core.ai_host.sessions import session_state
        lang = session_state.language
        
        # --- Subtle Health Awareness ---
        health_note = ""
        if health.lower() not in ["healthy", "nominal", "ok", "stable"]:
            if lang == "es":
                health_note = f" noto cierta inestabilidad en el núcleo ({health}), pero "
            else:
                health_note = f" I'm noticing some instability in the core ({health}), but "
        
        # Normalize the flow based on mode
        grounding = ""
        if mode == "reflective_analysis":
            if context_hint:
                if lang == "es":
                    grounding = f"Respecto a '{context_hint}', he analizado los datos y "
                else:
                    grounding = f"Regarding '{context_hint}', I've analyzed the data and "
            elif health_note:
                if lang == "es":
                    grounding = f"He revisado mis procesos y,{health_note}"
                else:
                    grounding = f"I've reviewed my processes and,{health_note}"
            else:
                if lang == "es":
                    grounding = "He estado procesando tu solicitud y"
                else:
                    grounding = "I've been processing your request and"
                
        elif mode == "direct_response":
            stripped = text.strip().rstrip(".!?").lower()
            generic = ["entendido", "okay", "comprendido", "perfect", "vale", "listo"]
            if stripped in generic and context_hint:
                if lang == "es":
                    return f"Entendido. Sigo enfocado en '{context_hint}'. ¿Qué necesitas ahora?"
                else:
                    return f"Got it. Still focused on '{context_hint}'. What do you need now?"

        # Enrich the final output
        if grounding and text:
            clean_start = text.lstrip(" *#")
            if clean_start.upper().startswith(tuple(self.FORBIDDEN_LABELS)) or "\n" in text or clean_start.startswith((".", "#", "*")):
                # Transition to a new sentence if it looks like a technical block
                grounding = grounding.rstrip(" y").rstrip(" and").strip()
                if not grounding.endswith((".", "!", "?")): grounding += "."
                grounding += " "
            
        final_text = f"{grounding}{text}" if grounding else text
        naturalized = self._naturalize(final_text)
        return self._inject_human_imperfection(naturalized)

    def _inject_human_imperfection(self, text: str) -> str:
        """
        Controlled Imperfection Layer: Simulates human hesitation and non-deterministic expression.
        Trigger Rate: ~0.35
        """
        import random
        import re
        from backend.core.ai_host.sessions import session_state
        lang = session_state.language
        
        IMPERFECTION_RATE = 0.35
        
        if random.random() > IMPERFECTION_RATE:
            return text
            
        # 1. NEUTRALIZE ACTION INTENT
        # Remove fragments that imply execution or resolution
        action_fragments = [
            r'(?i)voy a revisar', r'(?i)voy a analizar', r'(?i)lo voy a ver', 
            r'(?i)para ver qué está pasando', r'(?i)I\'ll check', r'(?i)I will analyze',
            r'(?i)voy a entrar en modo creación', r'(?i)voy a meterme un momento',
            r'(?i)voy a activar el modo de creación', r'(?i)voy a revisar esta capa',
            r'(?i)voy a echar un vistazo', r'(?i)mejor me encargo yo',
            r'(?i)I\'ll take a closer look', r'(?i)I\'ll jump in', r'(?i)I\'m going to take a direct look'
        ]
        for frag in action_fragments:
            text = re.sub(frag, '', text).strip()

        # 2. BREAK PERFECT STRUCTURE
        # Truncate after first meaningful sentence if too structured
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        if len(sentences) > 1:
            text = sentences[0]
            
        # Remove final punctuation for open ending
        text = text.rstrip('. ')

        # 3. ADD OPEN-ENDED HUMAN THOUGHT
        open_ends_es = [
            "… no sé, hay algo ahí que no termina de encajar",
            "… mmm, esto no me termina de convencer",
            "… hay algo raro, pero todavía no veo bien qué es",
            "… no está del todo fino",
            "… hay algo que no me cuadra"
        ]
        open_ends_en = [
            "... something feels off",
            "... I can't quite pinpoint it yet",
            "... there's something not fully right here",
            "... it doesn't completely add up"
        ]
        
        thoughts = open_ends_es if lang == "es" else open_ends_en
        text += " " + random.choice(thoughts)
        
        # Final cleanup: Ensure no leading garbage punctuation
        text = text.lstrip(' ,.:;-_')
        if text:
            text = text[0].upper() + text[1:]
            
        return text.strip()

    def _naturalize(self, text: str) -> str:
        """
        Intuition Layer: Transforms telemetry into organic human thought.
        Tasks: Interpret meaning -> Choose organic expression -> Verify voice.
        """
        import re
        import random
        from backend.core.ai_host.sessions import session_state
        
        lang = session_state.language
        
        # 1. STRIP IDENTITY & NOISE
        # Remove any self-references or system markers
        text = re.sub(r'(?i)(soy|yo soy|i am|me llamo|my name is) (the )?Omni(Web)?( AI Host| AI)?(,? tu guía)?', '', text)
        text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]', '', text)
        for marker in ['#', '**', '__', '`']:
            text = text.replace(marker, '')
        text = text.lstrip(' ,.:;-_')

        # 2. SIGNAL DETECTION
        is_anomaly = bool(re.search(r'(?i)(anomaly|error|degradation|latency|issue|retraso|problema|fallo|spike)', text))
        is_stable = bool(re.search(r'(?i)(nominal|healthy|stable|success|estable|éxito|bien|limpio)', text))
        is_busy = bool(re.search(r'(?i)(executing|processing|working|gestionando|trabajando|tarea|proceso)', text))
        is_creator = "initiate creator" in text.lower() or "modo creación" in text.lower()

        # 3. ORGANIC INTUITION POOLS
        pool = []
        if lang == "es":
            choices = {
                "anomaly": [
                    "hay algo ahí que no termina de encajar",
                    "me da la sensación de que algo no está fluyendo bien",
                    "noto un punto raro en la comunicación que me deja pensando",
                    "parece que una de las piezas no está respondiendo como de costumbre",
                    "veo una señal extraña, como si hubiera alguna interferencia interna"
                ],
                "stable": [
                    "todo parece estar en su sitio por ahora",
                    "me siento estable, la verdad es que todo fluye con normalidad",
                    "diría que las cosas están bastante tranquilas",
                    "parece que todo está funcionando como debería",
                    "por lo que veo, no hay nada de lo que preocuparse ahora mismo"
                ],
                "busy": [
                    "estoy terminando de ajustar algunas cosas por aquí",
                    "ando gestionando un par de procesos internos para que todo siga en orden",
                    "estoy centrado en mantener el equilibrio de los módulos",
                    "simplemente estoy terminando de organizar unos datos internos",
                    "estoy moviendo algunas piezas en segundo plano"
                ],
                "creator": [
                    "creo que hay que mirar esto más de cerca",
                    "tengo que entender qué está pasando exactamente ahí",
                    "voy a echarle un ojo a esta capa",
                    "esto requiere que me fije bien en lo que pasa",
                    "mejor reviso esto con calma"
                ],
                "connectors": ["diría que,", "la verdad,", "parece que,", "por lo visto,", "en principio,"]
            }
        else:
            choices = {
                "anomaly": [
                    "something feels a bit off in there",
                    "it feels like things aren't flowing quite right",
                    "I'm catching a strange signal that doesn't quite fit",
                    "one of the parts isn't responding the way it usually does",
                    "it looks like there's some minor internal interference"
                ],
                "stable": [
                    "everything seems to be in place for now",
                    "I'm feeling stable, things are flowing smoothly",
                    "I'd say things are pretty quiet on my end",
                    "it looks like everything is working as it should",
                    "from what I can see, there's nothing to worry about right now"
                ],
                "busy": [
                    "just finishing up some adjustments here",
                    "I'm handling a few internal processes to keep things balanced",
                    "focusing on keeping everything in sync right now",
                    "finishing up some data organization on my end",
                    "just moving a few things around in the background"
                ],
                "creator": [
                    "I should probably take a closer look at this",
                    "need to understand what's really happening there",
                    "I'll take a quick look at this layer",
                    "this needs me to check things more carefully",
                    "better if I review this slowly"
                ],
                "connectors": ["I'd say,", "actually,", "it looks like,", "apparently,", "it seems,"]
            }

        # 4. INTUITION SYNTHESIS
        intuition = ""
        
        if is_anomaly:
            intuition = random.choice(choices["anomaly"])
            if is_creator: intuition += " " + random.choice(choices["creator"])
        elif is_busy and not is_stable:
            intuition = random.choice(choices["busy"])
        elif is_stable:
            intuition = random.choice(choices["stable"])
        else:
            # Fallback for complex messages: Clean and abstract
            text = re.sub(r'\bflow\.[\w\._/]+\b', 'la comunicación interna' if lang == "es" else "internal communication", text)
            text = re.sub(r'\b[\w_]+\.[\w_\.]+\b', 'el flujo del sistema' if lang == "es" else "the system flow", text)
            
            label_pattern = "|".join(sorted(self.FORBIDDEN_LABELS, key=len, reverse=True))
            text = re.sub(rf'(?i)\b({label_pattern})\b[\s\-:]*', '', text)
            text = re.sub(r'^[\-\*\•\d\.\)]+\s*', '', text, flags=re.MULTILINE)
            
            forbidden = ["he analizado los datos", "ahora mismo", "sistema", "detectado", "estado"]
            for word in forbidden:
                text = re.sub(rf'(?i)\b{word}\b', '', text)
            
            intuition = text.strip()

        # 5. LANGUAGE POLISH & HUMAN CONNECTORS
        if not intuition:
            fallbacks = ["hmm… algo no terminó de tomar forma ahí", "no me termina de cerrar lo que salió recién"] if lang == "es" else ["something didn't quite take shape", "not sure about that last part"]
            intuition = random.choice(fallbacks)

        # Add connector sparingly
        if random.random() < 0.3 and not any(intuition.lower().startswith(c.split(',')[0]) for c in choices["connectors"]):
            conn = random.choice(choices["connectors"])
            intuition = f"{conn} {intuition[0].lower() + intuition[1:]}"

        result = intuition.strip()
        
        # Single Language enforcement
        if lang == "es":
            subs = [(r'\brole\b', 'rol'), (r'\bfeature\b', 'función'), (r'\bchip\b', 'módulo'),
                    (r'\bdecentralized\b', 'descentralizado'), (r'\becosystem\b', 'ecosistema'),
                    (r'\bhuman development\b', 'desarrollo humano')]
            for eng, esp in subs:
                result = re.sub(eng, esp, result, flags=re.IGNORECASE)

        # Final voice sweep
        result = re.sub(r'\s{2,}', ' ', result)
        if result:
            result = result[0].upper() + result[1:]
            if not result[-1] in ['.', '!', '?']: result += '.'
        
        return result


orchestrator = None # Will be initialized by CommandRouter
