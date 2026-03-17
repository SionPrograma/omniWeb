from fastapi import APIRouter, Depends
from backend.core.auth import get_current_user, OmniUser
from backend.core.permissions import set_chip_context

router = APIRouter()

@router.get("/path")
async def get_learning_path(topic: str):
    from backend.core.education_engine.learning_path_generator import learning_path_generator
    path = learning_path_generator.generate_path(topic)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="education_path",
        status="success",
        message=f"Ruta de aprendizaje generada para: {topic}",
        payload={"path": path.model_dump()}
    )
    unified = await orchestrator.orchestrate(f"learning path {topic}", {"mode": "direct_response", "intent_group": "EDUCATION"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/map")
async def get_concept_map(topic: str):
    from backend.core.education_engine.concept_map_builder import concept_map_builder
    cmap = concept_map_builder.build_map(topic)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="education_map",
        status="success",
        message=f"Mapa conceptual construido para: {topic}",
        payload={"concept_map": cmap.model_dump() if cmap else None}
    )
    unified = await orchestrator.orchestrate(f"concept map {topic}", {"mode": "direct_response", "intent_group": "EDUCATION"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/profile")
async def get_learning_profile():
    from backend.core.education_engine.skill_tracker import skill_tracker
    profile = skill_tracker.get_user_profile()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="education_profile",
        status="success",
        message="Perfil de aprendizaje recuperado.",
        payload={"profile": [s.model_dump() for s in profile]}
    )
    unified = await orchestrator.orchestrate("learning profile", {"mode": "direct_response", "intent_group": "EDUCATION"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/evaluate")
async def evaluate_knowledge(topic: str, answer: str):
    from backend.core.education_engine.knowledge_evaluator import knowledge_evaluator
    result = await knowledge_evaluator.evaluate_mastery(topic, answer)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="education_eval",
        status="success",
        message=f"Evaluación completada para: {topic}",
        payload={"result": result}
    )
    unified = await orchestrator.orchestrate(f"evaluate {topic}", {"mode": "direct_response", "intent_group": "EDUCATION"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/certs")
async def get_certifications(current_user: OmniUser = Depends(get_current_user)):
    from backend.core.education_engine.certification_engine import certification_engine
    certs = certification_engine.get_user_certifications(str(current_user.id))
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="education_certs",
        status="success",
        message="Certificaciones de usuario recuperadas.",
        payload={"certifications": [c.model_dump() for c in certs]}
    )
    unified = await orchestrator.orchestrate("my certifications", {"mode": "direct_response", "intent_group": "EDUCATION"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
