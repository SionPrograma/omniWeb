import pytest
from backend.core.education_engine.learning_path_generator import learning_path_generator
from backend.core.education_engine.concept_map_builder import concept_map_builder
from backend.core.education_engine.skill_tracker import skill_tracker
from backend.core.education_engine.knowledge_evaluator import knowledge_evaluator
from backend.core.education_engine.certification_engine import certification_engine
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_learning_path_generation():
    topic = "Physics"
    path = learning_path_generator.generate_path(topic)
    assert path.topic == topic
    assert len(path.steps) > 0
    assert path.steps[0].title.startswith("Introduction")

def test_concept_map_generation():
    topic = "Physics"
    cmap = concept_map_builder.build_map(topic, depth=1)
    assert cmap is not None
    assert cmap.name == topic

def test_skill_tracking():
    concept = "TestConcept"
    skill_tracker.update_skill(concept, increment_xp=50, level_boost=0.2)
    profile = skill_tracker.get_user_profile()
    skill = next((s for s in profile if s.concept == concept), None)
    assert skill is not None
    assert skill.experience_points >= 50
    assert skill.level >= 0.2

@pytest.mark.asyncio
async def test_knowledge_evaluation():
    topic = "Thermodynamics"
    user_input = "Thermodynamics is the study of energy, heat, work, and their transformations in physical systems."
    result = await knowledge_evaluator.evaluate_mastery(topic, user_input)
    assert result["success"] == True
    assert result["score"] > 0.4

def test_certification_logic():
    import uuid
    user_id = str(uuid.uuid4())
    # Force a skill to 1.0
    concept = f"Robotics_{uuid.uuid4().hex[:4]}"
    skill_tracker.update_skill(concept, level_boost=1.0)
    
    certs = certification_engine.check_for_certifications(user_id)
    assert any(c.title == f"{concept.capitalize()} Mastery Certification" for c in certs)
