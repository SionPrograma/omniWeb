import json
import logging
import httpx
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ValidationError
from backend.core.config import settings

logger = logging.getLogger(__name__)

class CognitiveAnalysisResult(BaseModel):
    """Contrato estricto del output cognitivo."""
    semantic_target: str = Field(description="Resumen interno de la intención real del humano")
    technical_hypothesis: str = Field(description="Deducción de qué sistema físico está involucrado o fallando")
    decision_mode: str = Field(description="Uno de: 'direct_response', 'reflective_analysis', 'action_execution', 'remediation', 'clarification', 'swarm_orchestration'")
    actionable_chips: List[str] = Field(default_factory=list, description="Lista de chips afectados, ej: ['chip-finanzas']")
    requires_clarification: bool = Field(default=False)
    confidence_score: float = Field(ge=0.0, le=1.0)
    constraints: List[str] = Field(default_factory=list)

class CognitiveBridge:
    """Corteza auxiliar L2 profunda. Conecta con Groq/Llama-3 para razonamiento estructurado."""
    
    def __init__(self):
        self.api_key = settings.COGNITIVE_API_KEY
        self.model = settings.COGNITIVE_MODEL
        self.timeout = settings.COGNITIVE_TIMEOUT_MS / 1000.0  # en segundos
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.enabled = bool(self.api_key)

    async def analyze_context(self, context_payload: str) -> CognitiveAnalysisResult:
        """Envía el contexto ensamblado al modelo, fuerza la salida estructurada y la valida."""
        if not self.enabled:
            logger.info("[COGNITIVE_BRIDGE] Ignorado: No hay API_KEY configurada.")
            raise ValueError("Cognitive bridge disabled.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "Eres el motor cognitivo de deducción técnica de OmniWeb. "
            "Devuelve ÚNICAMENTE un objeto JSON válido analizando el contexto de sesión dado.\n"
            "Formato JSON requerido:\n"
            "{\n"
            "  \"semantic_target\": \"string\",\n"
            "  \"technical_hypothesis\": \"string\",\n"
            "  \"decision_mode\": \"direct_response | reflective_analysis | action_execution | remediation | clarification | swarm_orchestration\",\n"
            "  \"actionable_chips\": [\"chip-ejemplo\"],\n"
            "  \"requires_clarification\": boolean,\n"
            "  \"confidence_score\": float (0.0 to 1.0),\n"
            "  \"constraints\": [\"string\"]\n"
            "}"
        )

        data = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_payload}
            ]
        }
        
        logger.debug(f"[COGNITIVE_BRIDGE] Iniciando llamada a L2 (timeout={self.timeout}s)...")
        # Preparamos client asíncrono
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                content_str = result["choices"][0]["message"]["content"]
                
                # Parseo crudo a dict
                raw_json = json.loads(content_str)
                
                # Validación estricta vía Pydantic
                structured_data = CognitiveAnalysisResult(**raw_json)
                
                # Post-guardas de seguridad
                structured_data = self._apply_guardrails(structured_data)
                
                return structured_data
                
        except httpx.TimeoutException:
            logger.warning("[COGNITIVE_BRIDGE] Falla por Timeout. Módulo L2 inestable.")
            raise
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"[COGNITIVE_BRIDGE] Falla de contrato JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"[COGNITIVE_BRIDGE] Error inesperado L2: {e}")
            raise

    def _apply_guardrails(self, data: CognitiveAnalysisResult) -> CognitiveAnalysisResult:
        """Aplica la validación autoritativa de OmniWeb sobre la salida del LLM."""
        
        # 1. Validar Chips contra el entorno real de OmniWeb
        from backend.core.config import settings as core_settings
        valid_chips = []
        for chip in data.actionable_chips:
            # Quitamos sufijos o prefijos basura que los LLMs suelen inventar
            clean_chip = chip.replace("chip-", "").strip().lower()
            if clean_chip in core_settings.ACTIVE_MODULES:
                valid_chips.append(f"chip-{clean_chip}")
        
        data.actionable_chips = valid_chips
        
        # 2. Whitelist estricta de Decision Mode
        allowed_modes = [
            "direct_response", "reflective_analysis", "action_execution", 
            "remediation", "clarification", "swarm_orchestration"
        ]
        if data.decision_mode not in allowed_modes:
            logger.warning(f"[COGNITIVE_BRIDGE] Modo inventado '{data.decision_mode}' ignorado. Forzando clarification.")
            data.decision_mode = "clarification"
            
        # 3. Forzar clarification si la confianza es baja
        if data.confidence_score < 0.70:
            data.requires_clarification = True
            
        return data

# Singleton
cognitive_bridge = CognitiveBridge()
