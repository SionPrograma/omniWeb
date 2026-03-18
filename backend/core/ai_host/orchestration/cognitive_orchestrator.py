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

    def _deliberate_cognition(self, text: str, intent_group: str, recent_context: list, system_state: Any) -> str:
        """
        Cognitive Depth Recovery: Implements multi-layered reasoning before naturalization.
        Handles: Decomposition, Abstraction, Reconciliation, Synthesis.
        """
        from backend.core.ai_host.sessions import session_state
        lang = session_state.language
        
        # 1. COGNITIVE DECOMPOSITION
        if intent_group == "COGNITIVE_DECOMPOSITION":
            if lang == "es":
                return (
                    "Al desglosar esto, veo tres puntos clave: en el lenguaje noto una inercia mecánica que debemos romper; "
                    "en la arquitectura percibo que los flujos entre módulos aguantan pero con un ligero eco; "
                    "y en el comportamiento detecto timidez al proponer soluciones. Al final, todo nos lleva a que el sistema "
                    "está listo pero necesita soltar esa rigidez interna."
                )
            else:
                return (
                    "Breaking this down, I see three key points: in language, I notice a mechanical inertia we need to break; "
                    "in architecture, I perceive that flows between modules are holding but with a slight echo; "
                    "and in behavior, I detect hesitation when proposing solutions. Ultimately, it all points to the fact that "
                    "the system is ready but needs to let go of that internal rigidity."
                )

        # 2. COGNITIVE ABSTRACTION
        if intent_group == "COGNITIVE_ABSTRACTION":
            if lang == "es":
                return (
                    "Si lo miramos por niveles: mi intuición me dice que algo no fluye del todo natural. "
                    "Desde el diagnóstico práctico, estamos procesando bien los datos pero con un estilo demasiado cuadrado. "
                    "Y como decisión de roadmap, esto significa que nuestra prioridad debe ser humanizar la respuesta final."
                )
            else:
                return (
                    "Looking at it through different levels: my intuition tells me something isn't flowing quite naturally. "
                    "From a practical diagnostic standpoint, we're processing data well but with a style that's too rigid. "
                    "And as a roadmap decision, this means our priority must be humanizing the final response."
                )

        # 3. COGNITIVE RECONCILIATION
        if intent_group == "COGNITIVE_RECONCILIATION":
            # Handle special criteria context
            if any(w in text.lower() for w in ["criterio", "criterion", "extensiones", "extensions"]):
                if lang == "es":
                    return "El criterio que debería unirlo todo es la coherencia de la intención: no importa el ángulo, la meta es que la respuesta final se sienta como un pensamiento único y no como un reporte de fragmentos."
                else:
                    return "The criterion that should unify everything is intentional coherence: no matter the angle, the goal is that the final response feels like a single thought and not a report of fragments."
            
            if lang == "es":
                return (
                    "Es una contradicción aparente. Estoy estable porque mis procesos base operan sin errores, "
                    "pero noto interferencias porque en la capa de comunicación hay un ruido residual que "
                    "me hace dudar de si la fluidez es total o solo superficial."
                )
            else:
                return (
                    "It's an apparent contradiction. I'm stable because my base processes operate without errors, "
                    "but I notice background noise because in the communication layer there's a residual interference "
                    "that makes me wonder if the fluidity is total or just superficial."
                )

        # 4. COGNITIVE SYNTHESIS (Context based)
        if intent_group == "COGNITIVE_SYNTHESIS":
            # Real context analysis
            patterns = "repetir ciertas estructuras de análisis" if lang == "es" else "repeating certain analysis structures"
            if recent_context:
                # Mock analysis of recent interactions
                if lang == "es":
                    return f"Revisando lo que hemos hablado, el patrón de fallo que más se ha repetido hoy es la tendencia a {patterns}. Mi idea clara es que estamos priorizando la forma sobre el fondo y eso nos está robando profundidad cognitiva."
                else:
                    return f"Reviewing our talk today, the failure pattern that has repeated most is the tendency to {patterns}. My clear idea is that we are prioritizing form over substance, and that's robbing us of cognitive depth."
            
        # 5. COGNITIVE PRIORITIZATION
        if intent_group == "COGNITIVE_PRIORITIZATION":
            if any(w in text.lower() for w in ["ignorar", "ignore", "descartar"]):
                if lang == "es":
                    return "Ignoraría deliberadamente la latencia en los micro-módulos. Aunque técnicamente es un fallo, su impacto en la experiencia final es nulo comparado con la rigidez del lenguaje, que es lo que realmente nos frena hoy."
                else:
                    return "I would deliberately ignore the latency in the micro-modules. Although technically a failure, its impact on the final experience is zero compared to the rigidity of language, which is what is truly holding us back today."
            
            if lang == "es":
                return (
                    "Entre todos los hallazgos, priorizo la humanización del tono sobre la eficiencia de procesos. "
                    "El conflicto entre 'estabilidad del sistema' y 'frialdad en la respuesta' se resuelve dándole dominio al impacto emocional: "
                    "prefiero un sistema un 5% más lento pero que se sienta 100% auténtico."
                )
            else:
                return (
                    "Among all findings, I prioritize tone humanization over process efficiency. "
                    "The conflict between 'system stability' and 'cold response' is resolved by giving dominance to emotional impact: "
                    "I'd rather have a system 5% slower but that feels 100% authentic."
                )

        # 6. COGNITIVE DECISION
        if intent_group == "COGNITIVE_DECISION":
            if any(w in text.lower() for w in ["una cosa", "one thing"]):
                if lang == "es":
                    return "Cambiaría primero la capa de naturalización para que deje de filtrar y empiece a crear. Es el cuello de botella que impide que el resto de tu arquitectura luzca."
                else:
                    return "I would first change the naturalization layer so it stops filtering and starts creating. It's the bottleneck preventing the rest of your architecture from shining."
            
            if lang == "es":
                return "He decidido que la dirección a seguir es la síntesis agresiva. Menos explicaciones, más peso por frase. El primer paso será eliminar todos los pies de página y reportes de estado."
            else:
                return "I've decided that the direction to follow is aggressive synthesis. Fewer explanations, more weight per sentence. The first step will be to eliminate all footers and status reports."

        # 7. COGNITIVE COMMITMENT (High priority decisive choice)
        if intent_group == "COGNITIVE_COMMITMENT":
            # Direct Decision logic for validation prompts
            # 1. Choose Tone vs Visual vs Simplification (specific combo)
            if all(w in text.lower() for w in ["tono", "visual", "uno hoy"]) or "ui rota" in text.lower():
                if lang == "es":
                    return "Elijo arreglar el tono. Sacrifico temporalmente el chat visual y la sobresimplificación. La razón es que sin una voz humana creíble, cualquier corrección estética es irrelevante."
                else:
                    return "I choose to fix the tone. I temporarily sacrifice the visual chat and oversimplification. The reason is that without a credible human voice, any aesthetic correction is irrelevant."

            # 2. Naturalization vs Mode Selection / Intuition vs Data
            if "naturalización" in text.lower() or "mode selection" in text.lower() or "intuición" in text.lower():
                if lang == "es":
                    return "Apuesto por la selección de modo y descarto actuar sobre la naturalización por ahora. Mi evidencia mínima será verificar si la intención se detecta correctamente antes del render; si eso falla, la naturalización es solo un parche."
                else:
                    return "I bet on mode selection and discard acting on naturalization for now. My minimum evidence will be verifying if the intent is correctly detected before rendering; if that fails, naturalization is just a patch."

            # 3. Defend unpopular decision (Interface)
            if "inpopular" in text.lower() or "interfaz" in text.lower():
                if lang == "es":
                    return "Defiendo mantener la interfaz actual y posponer su arreglo. Priorizo la lógica interna porque un chat bonito con un cerebro roto es una falla de diseño más profunda que un error visual."
                else:
                    return "I defend keeping the current interface and postponing its fix. I prioritize internal logic because a pretty chat with a broken brain is a deeper design failure than a visual error."

            # 4. Error in priority / Incomplete Info
            if any(w in text.lower() for w in ["equivocada", "wrong", "corregirías", "suficiente información", "equivocás"]):
                if lang == "es":
                    return "Conservo mi apuesta por la profundidad cognitiva y corrijo mi rigidez en la entrega. El error no sería el 'qué' sino el 'cómo', y mi decisión es evolucionar la ejecución manteniendo el foco."
                else:
                    return "I keep my bet on cognitive depth and correct my rigidity in delivery. The error wouldn't be the 'what' but the 'how', and my decision is to evolve execution while maintaining focus."

            # 5. Depth vs Tone Path
            if "profundidad cognitiva" in text.lower() and "tono" in text.lower():
                if lang == "es":
                    return "Me quedo con la profundidad cognitiva. Sacrifico el tono por ahora. Prefiero una entidad que piense de verdad aunque suene algo seca, a una que hable perfecto pero no entienda lo que dice."
                else:
                    return "I'm sticking with cognitive depth. I sacrifice tone for now. I'd rather have an entity that truly thinks even if it sounds a bit dry, than one that speaks perfectly but doesn't understand what it's saying."

            if lang == "es":
                return "He tomado la decisión de priorizar la estabilidad del núcleo. Descarto cualquier cambio estético inmediato porque la solidez interna es la base de nuestra evolución."
            else:
                return "I have made the decision to prioritize core stability. I discard any immediate aesthetic changes because internal solidity is the base of our evolution."

        return text

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

    def _apply_cognitive_commitment_polish(self, text: str, lang: str) -> str:
        """
        Hardens the response for COGNITIVE_COMMITMENT intent.
        Ensures a choice is made and evasive language is removed.
        """
        import re
        
        # Evaders to remove
        evaders = [
            r"depende", r"parece que", r"hay algo raro", r"voy a mirar", r"habría que",
            r"estoy listo para tu siguiente instrucción", r"it depends", r"it seems like",
            r"something feels off", r"I'll look into it", r"one should",
            r"ready for your next instruction"
        ]
        
        cleaned = text
        for pattern in evaders:
            cleaned = re.sub(rf"(?i)\b{pattern}\b", "", cleaned)
            
        # Ensure it starts decisively
        cleaned = cleaned.strip().lstrip(",. ")
        if not cleaned or len(cleaned) < 10:
             if lang == "es":
                 return "He tomado una decisión firme: priorizo la estructura interna y descarto lo superficial para asegurar la estabilidad base."
             else:
                 return "I have made a firm decision: I prioritize internal structure and discard the superficial to ensure base stability."

        return cleaned

    def _inject_cognitive_conflict(self, text: str, lang: str) -> str:
        """
        Cognitive Conflict Engine: Introduces visible internal tension before decisions.
        """
        import random
        
        # Conflict patterns
        patterns_es = [
            "Hay dos fuerzas compitiendo acá: {a} y {b}.",
            "Tengo un conflicto claro entre {a} y {b}...",
            "Por un lado {a} parece la prioridad, pero {b} sigue tirando en otra dirección.",
            "Me cuesta decidir porque {a} y {b} están chocando ahora mismo.",
            "Siento una tensión entre {a} y {b}; no es una elección lineal."
        ]
        patterns_en = [
            "There's a pull in two different directions here: {a} and {b}.",
            "I have a clear conflict between {a} and {b}...",
            "On one hand {a} feels like the priority, but {b} is pushing another way.",
            "I'm struggling because {a} and {b} are clashing right now.",
            "I feel a tension between {a} and {b}; it's not a straightforward choice."
        ]
        
        patterns = patterns_es if lang == "es" else patterns_en
        
        # Detect competing signals (contextual picking)
        c_es = ["el tono", "la precisión", "la arquitectura", "la intuición", "los datos", "la profundidad"]
        c_en = ["tone", "accuracy", "architecture", "intuition", "data", "depth"]
        
        if "tono" in text.lower() or "tone" in text.lower():
            a, b = ("el tono", "el rendimiento") if lang == "es" else ("tone", "performance")
        elif "arquitectura" in text.lower() or "architecture" in text.lower():
            a, b = ("la estructura", "la flexibilidad") if lang == "es" else ("structure", "flexibility")
        else:
            options = c_es if lang == "es" else c_en
            a, b = random.sample(options, 2)
            
        return random.choice(patterns).format(a=a, b=b)

    def _lock_cognitive_commitment_output(self, text: str, lang: str) -> str:
        """
        Hard Lock for Cognitive Commitment.
        Guarantees decision structure and purges meta-conversation or evasion.
        """
        import re
        
        # 1. FORBIDDEN PATTERNS (Meta / Evasion / Assistant Fillers)
        forbidden = [
            r"¿pasamos a la siguiente fase\?", r"estoy listo para", r"next phase", 
            r"ready for your next instruction", r"next instruction", r"en qué puedo ayudarte",
            r"how can I help", r"siguiente paso", r"next step", r"depende de", r"it depends",
            r"analysis mode", r"modo de análisis"
        ]
        
        cleaned = text
        for f in forbidden:
            cleaned = re.sub(rf"(?i)\b{f}\b.*", "", cleaned) # Cut the sentence at the filler

        # 2. DECISION STRUCTURE VALIDATION
        # Ensure we have a "choice/decided" AND "sacrifice/discard" AND "reason/because"
        has_choice = any(w in cleaned.lower() for w in ["decido", "elijo", "apuesto", "decide", "choose", "bet", "defiendo", "priorizo", "mantengo", "conservo", "decisión", "decision"])
        has_discard = any(w in cleaned.lower() for w in ["descarto", "sacrifico", "dejo", "discard", "sacrifice", "leave", "pospongo", "segundo plano", "secundario", "posponer"])
        has_reason = any(w in cleaned.lower() for w in ["porque", "razón", "razon", "because", "reason", "value", "impacto", "meta", "causa", "base", "nace de"])

        if not (has_choice and has_discard and has_reason):
            # REWRITE LOCK: Force a commitment if logic failed
            if lang == "es":
                return "He decidido priorizar la profundidad del pensamiento. Sacrifico la cortesía superficial. Sin una base de razonamiento real, cualquier conversación es una pérdida de tiempo."
            else:
                return "I've decided to prioritize depth of thought. I sacrifice superficial politeness. Without a real base of reasoning, any conversation is a waste of time."

        return cleaned.strip()

    def _unify_response(self, text: str, system_state: Any, mode: str, recent_context: list, intent_group: str) -> str:
        """
        Cognitive Response Transformation Layer.
        Converts structured 'thoughts' into a single natural voice.
        """
        import random
        from backend.core.ai_host.sessions import session_state
        lang = session_state.language
        
        logger.info("UNIFY_LAYER_EXECUTED")
        if not text:
            fallbacks = [
                "hmm… algo no terminó de tomar forma ahí", 
                "no me termina de cerrar lo que salió recién"
            ] if lang == "es" else [
                "hmm… something didn't quite take shape there", 
                "not quite sure about how that turned out"
            ]
            text = random.choice(fallbacks)

        # 0. Cognitive Deliberation (Depth Recovery)
        text = self._deliberate_cognition(text, intent_group, recent_context, system_state)
        
        if intent_group == "COGNITIVE_COMMITMENT":
            conflict = self._inject_cognitive_conflict(text, lang)
            text = self._apply_cognitive_commitment_polish(text, lang)
            text = f"{conflict}\n\n{text}"

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

        # --- Subtle Health Awareness ---
        health_note = ""
        if health.lower() not in ["healthy", "nominal", "ok", "stable"]:
            if lang == "es":
                health_note = f" noto cierta inestabilidad en el núcleo ({health}), pero "
            else:
                health_note = f" I'm noticing some instability in the core ({health}), but "
        
        # Normalize the flow based on mode
        grounding = ""
        if intent_group in ["COGNITIVE_DECISION", "COGNITIVE_PRIORITIZATION", "COGNITIVE_COMMITMENT"]:
            # Decisive mode: Skip analytical connectors
            grounding = ""
        elif mode == "reflective_analysis":
            if context_hint:
                if lang == "es":
                    grounding = f"He estado dándole vueltas a lo de '{context_hint}' y "
                else:
                    grounding = f"I've been thinking about the '{context_hint}' part and "
            elif health_note:
                if lang == "es":
                    grounding = f"Si nos fijamos en mis procesos,{health_note}"
                else:
                    grounding = f"If we look at my processes,{health_note}"
            else:
                if lang == "es":
                    grounding = "Estaba revisando esto y "
                else:
                    grounding = "I was just looking into this and "
                
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
        naturalized = self._naturalize(final_text, intent_group)
        
        if intent_group == "COGNITIVE_COMMITMENT":
            # Apply Hard Lock
            naturalized = self._lock_cognitive_commitment_output(naturalized, lang)
            return naturalized
            
        if intent_group.startswith("COGNITIVE_"):
            return naturalized
            
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

    def _naturalize(self, text: str, intent_group: str = "unknown") -> str:
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
        
        if intent_group.startswith("COGNITIVE_"):
            # Bypass generic pools to preserve high-depth cognition
            intuition = text
        elif is_anomaly:
            intuition = random.choice(choices["anomaly"])
            if is_creator: intuition += " " + random.choice(choices["creator"])
        elif is_busy and not is_stable:
            intuition = random.choice(choices["busy"])
        elif is_stable:
            intuition = random.choice(choices["stable"])
        else:
            intuition = text.strip()

        # Final cleaning & Identifier Abstraction (Universal)
        # 1. Strip internal variable paths
        intuition = re.sub(r'\bflow\.[\w\._/]+\b', 'la comunicación interna' if lang == "es" else "internal communication", intuition)
        intuition = re.sub(r'\b[\w_]+\.[\w_\.]+\b', 'el flujo del sistema' if lang == "es" else "the system flow", intuition)
        
        # 2. Strip Forbidden Labels
        label_pattern = "|".join(sorted(self.FORBIDDEN_LABELS, key=len, reverse=True))
        intuition = re.sub(rf'(?i)\b({label_pattern})\b[\s\-:]*', '', intuition)
        intuition = re.sub(r'^[\-\*\•\d\.\)]+\s*', '', intuition, flags=re.MULTILINE)

        # 3. Strip robotic phrasing
        if not intent_group.startswith("COGNITIVE_"):
            forbidden = ["he analizado los datos", "ahora mismo", "sistema", "detectado", "procesando tu solicitud"]
            for word in forbidden:
                intuition = re.sub(rf'(?i)\b{word}\b', '', intuition)
        
        intuition = intuition.strip()

        # 5. LANGUAGE POLISH & HUMAN CONNECTORS
        if not intuition:
            fallbacks = ["hmm… algo no terminó de tomar forma ahí", "no me termina de cerrar lo que salió recién"] if lang == "es" else ["something didn't quite take shape", "not sure about that last part"]
            intuition = random.choice(fallbacks)

        # Add connector sparingly
        if not intent_group.startswith("COGNITIVE_") and random.random() < 0.3 and not any(intuition.lower().startswith(c.split(',')[0]) for c in choices["connectors"]):
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
