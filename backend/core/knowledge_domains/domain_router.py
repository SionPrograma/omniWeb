from fastapi import APIRouter, HTTPException, Depends
from .domain_registry import domain_registry
from .domain_summary_engine import domain_summary_engine
from .domain_models import KnowledgeDomain, DomainSummary
from backend.core.auth import get_current_user, OmniUser

router = APIRouter()

@router.get("/")
async def list_domains(current_user: OmniUser = Depends(get_current_user)):
    domains = domain_registry.list_domains()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="list_knowledge_domains",
        status="success",
        message=f"Se han identificado {len(domains)} dominios de conocimiento activos.",
        payload={"domains": [d.dict() if hasattr(d, 'dict') else d for d in domains]}
    )
    unified = await orchestrator.orchestrate("list knowledge domains", {"mode": "direct_response", "intent_group": "KNOWLEDGE"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/{domain_id}")
async def get_domain(domain_id: str, current_user: OmniUser = Depends(get_current_user)):
    domain = domain_registry.get_domain(domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
        
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_knowledge_domain",
        status="success",
        message=f"Detalles del dominio '{domain.name}' recuperados.",
        payload=domain.dict() if hasattr(domain, 'dict') else domain
    )
    unified = await orchestrator.orchestrate(f"get knowledge domain {domain_id}", {"mode": "direct_response", "intent_group": "KNOWLEDGE"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/{domain_id}/summary")
async def get_domain_summary(domain_id: str, current_user: OmniUser = Depends(get_current_user)):
    summary = await domain_summary_engine.generate_summary(domain_id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_knowledge_domain_summary",
        status="success",
        message=f"Resumen cognitivo del dominio {domain_id} generado.",
        payload=summary.dict() if hasattr(summary, 'dict') else summary
    )
    unified = await orchestrator.orchestrate(f"get summary of knowledge domain {domain_id}", {"mode": "direct_response", "intent_group": "KNOWLEDGE"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
