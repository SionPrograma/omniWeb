from fastapi import APIRouter, Security, Depends, HTTPException
from typing import List, Optional, Dict, Any
from backend.core.security.dependencies import get_current_user, get_creator_user
from backend.core.auth import OmniUser
from backend.core.knowledge_os.knowledge_store import knowledge_store
from backend.core.knowledge_graph.processor import global_graph_processor
from backend.core.education_engine.learning_path import learning_path_engine
from backend.core.certification_engine.manager import certification_engine
from backend.core.opportunity_engine.processor import opportunity_engine
from backend.core.interface.accessibility import accessibility_layer

router = APIRouter()

@router.get("/knowledge/units")
async def get_knowledge_units(k_type: Optional[str] = None, current_user: OmniUser = Depends(get_current_user)):
    units = await knowledge_store.get_units(k_type)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="human_knowledge_units",
        status="success",
        message="Unidades de conocimiento recuperadas.",
        payload={"units": units}
    )
    unified = await orchestrator.orchestrate("get knowledge units", {"mode": "direct_response", "intent_group": "HUMAN_DEV"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/graph/galaxy")
async def get_graph_galaxy(current_user: OmniUser = Depends(get_current_user)):
    data = await global_graph_processor.get_graph_data()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="human_graph_galaxy",
        status="success",
        message="Visualización de la galaxia de conocimiento lista.",
        payload=data
    )
    unified = await orchestrator.orchestrate("show knowledge galaxy", {"mode": "direct_response", "intent_group": "HUMAN_DEV"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/learning/paths")
async def get_learning_paths(current_user: OmniUser = Depends(get_current_user)):
    paths = await learning_path_engine.get_user_paths(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="human_learning_paths",
        status="success",
        message="Tus rutas de aprendizaje activas han sido cargadas.",
        payload={"paths": paths}
    )
    unified = await orchestrator.orchestrate("get learning paths", {"mode": "direct_response", "intent_group": "HUMAN_DEV"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/opportunities")
async def get_opportunities(current_user: OmniUser = Depends(get_current_user)):
    opportunities = await opportunity_engine.match_opportunities(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="human_opportunities",
        status="success",
        message="Oportunidades de desarrollo identificadas para tu perfil.",
        payload={"opportunities": opportunities}
    )
    unified = await orchestrator.orchestrate("find opportunities", {"mode": "direct_response", "intent_group": "HUMAN_DEV"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/accessibility/profile")
async def get_accessibility(current_user: OmniUser = Depends(get_current_user)):
    profile = await accessibility_layer.get_profile(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="human_accessibility_get",
        status="success",
        message="Perfil de accesibilidad recuperado.",
        payload=profile
    )
    unified = await orchestrator.orchestrate("get accessibility profile", {"mode": "direct_response", "intent_group": "HUMAN_DEV"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/accessibility/profile")
async def update_accessibility(data: Dict[str, Any], current_user: OmniUser = Depends(get_current_user)):
    await accessibility_layer.update_profile(current_user.id, data)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="human_accessibility_update",
        status="success",
        message="Perfil de accesibilidad actualizado correctamente.",
        payload={"status": "success"}
    )
    unified = await orchestrator.orchestrate("update accessibility profile", {"mode": "direct_response", "intent_group": "HUMAN_DEV"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
