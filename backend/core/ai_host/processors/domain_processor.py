import logging
from backend.core.knowledge_domains.domain_registry import domain_registry, DomainCategory
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class DomainProcessor(CommandProcessor):
    """Bridges AI Host commands to the Knowledge Domains system."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg = msg.lower()
        
        # 1. List Domains
        if "mostrar dominios" in msg or "list domains" in msg:
            domains = domain_registry.list_domains()
            domain_list = ", ".join([d.name for d in domains])
            return AICommandResponse(
                intent="domains_list",
                message=f"Los dominios actuales de conocimiento global son: {domain_list}.",
                status="success",
                payload={"domains": [d.model_dump() for d in domains]}
            )

        # 2. Domain Details
        if "ciencia" in msg:
            domain = domain_registry.get_domain(DomainCategory.SCIENCE)
            return AICommandResponse(
                intent="domain_info",
                message=f"Accediendo al dominio de Ciencia: {domain.description}",
                status="success"
            )

        return AICommandResponse(
            intent="domain_general",
            message="Comando de dominios no reconocido. Prueba con 'mostrar dominios'.",
            status="partial"
        )

domain_processor = DomainProcessor()
