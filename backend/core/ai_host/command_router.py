from typing import Dict, Any, Optional, List
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AICommandResponse(BaseModel):
    intent: str
    status: str
    message: str
    payload: Dict[str, Any] = {}

class CommandRouter:
    """
    Parses and routes natural language commands to system actions.
    """
    def __init__(self):
        self.intents = {
            "open": self._handle_open,
            "create": self._handle_create,
            "activate": self._handle_activate,
            "deactivate": self._handle_deactivate,
            "status": self._handle_status,
            "list": self._handle_list,
            "workflow": self._handle_workflow
        }

    async def route(self, message: str) -> AICommandResponse:
        msg = message.lower()
        res = None
        
        # Simple rule-based intent classification
        if "abrir" in msg or "open" in msg:
             res = await self.intents["open"](msg)
        elif "crea" in msg or "create" in msg:
             res = await self.intents["create"](msg)
        elif "activa" in msg or "activate" in msg:
             res = await self.intents["activate"](msg)
        elif "desactiva" in msg or "deactivate" in msg:
             res = await self.intents["deactivate"](msg)
        elif "estado" in msg or "status" in msg or "salud" in msg:
             res = await self.intents["status"](msg)
        elif "listar" in msg or "list" in msg or "chips" in msg:
             res = await self.intents["list"](msg)
        elif "workflow" in msg or "flujo" in msg or "sesión" in msg:
             res = await self.intents["workflow"](msg)
        
        if not res:
            res = AICommandResponse(
                intent="unknown",
                status="error",
                message="Lo siento, no entiendo ese comando.",
                payload={}
            )

        # Telemetry (Phase F)
        try:
            from backend.core.usage.usage_tracker import usage_tracker
            usage_tracker.log_event(
                event_type="ai_command_executed",
                chip_slug="ai-host",
                metadata={
                    "intent": res.intent,
                    "status": res.status,
                    "message_preview": message[:50] # Privacy first
                }
            )
        except:
            pass

        return res

    async def _handle_open(self, msg: str) -> AICommandResponse:
        target = "none"
        if "finanzas" in msg or "finances" in msg: target = "finanzas"
        elif "reparto" in msg or "delivery" in msg: target = "reparto"
        elif "musica" in msg or "music" in msg: target = "musica"
        
        if target != "none":
            return AICommandResponse(
                intent="open_chip",
                status="success",
                message=f"Abriendo el chip {target}.",
                payload={"target": target, "action": "ACTIVATE_CHIP"}
            )
        return AICommandResponse(intent="open_chip", status="error", message="No encontré el chip a abrir.")

    async def _handle_create(self, msg: str) -> AICommandResponse:
        # Calls Chip Factory
        from backend.core.chip_factory import chip_factory
        result = await chip_factory.create_from_request(msg)
        if result["status"] == "success":
             return AICommandResponse(
                 intent="create_chip",
                 status="success",
                 message=result["message"],
                 payload={"chip": result["chip"]}
             )
        return AICommandResponse(intent="create_chip", status="error", message=result["detail"])

    async def _handle_activate(self, msg: str) -> AICommandResponse:
        # Implementation in Step 3
        return AICommandResponse(intent="activate_chip", status="pending", message="Funcionalidad de activación en desarrollo.")

    async def _handle_deactivate(self, msg: str) -> AICommandResponse:
        return AICommandResponse(intent="deactivate_chip", status="pending", message="Funcionalidad de desactivación en desarrollo.")

    async def _handle_status(self, msg: str) -> AICommandResponse:
        return AICommandResponse(intent="system_status", status="success", message="El sistema está operativo y saludable.", payload={})

    async def _handle_list(self, msg: str) -> AICommandResponse:
        from backend.core.module_registry import module_registry
        chips = module_registry.discover_all_chips()
        chip_names = [c["name"] for c in chips]
        return AICommandResponse(
            intent="list_chips",
            status="success",
            message=f"Chips instalados: {', '.join(chip_names)}",
            payload={"chips": chips}
        )

    async def _handle_workflow(self, msg: str) -> AICommandResponse:
        return AICommandResponse(intent="workflow_execute", status="pending", message="Motor de workflows en desarrollo.")

ai_command_router = CommandRouter()
