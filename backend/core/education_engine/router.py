from fastapi import APIRouter, Depends
from backend.core.auth import get_current_user, OmniUser
from backend.core.permissions import set_chip_context

router = APIRouter()

@router.get("/path")
async def get_learning_path(topic: str):
    from backend.core.education_engine.learning_path_generator import learning_path_generator
    path = learning_path_generator.generate_path(topic)
    return {"status": "ok", "path": path.model_dump()}

@router.get("/map")
async def get_concept_map(topic: str):
    from backend.core.education_engine.concept_map_builder import concept_map_builder
    cmap = concept_map_builder.build_map(topic)
    return {"status": "ok", "concept_map": cmap.model_dump() if cmap else None}

@router.get("/profile")
async def get_learning_profile():
    from backend.core.education_engine.skill_tracker import skill_tracker
    profile = skill_tracker.get_user_profile()
    return {"status": "ok", "profile": [s.model_dump() for s in profile]}

@router.post("/evaluate")
async def evaluate_knowledge(topic: str, answer: str):
    from backend.core.education_engine.knowledge_evaluator import knowledge_evaluator
    result = await knowledge_evaluator.evaluate_mastery(topic, answer)
    return {"status": "ok", "result": result}

@router.get("/certs")
async def get_certifications(current_user: OmniUser = Depends(get_current_user)):
    from backend.core.education_engine.certification_engine import certification_engine
    certs = certification_engine.get_user_certifications(str(current_user.id))
    return {"status": "ok", "certifications": [c.model_dump() for c in certs]}
