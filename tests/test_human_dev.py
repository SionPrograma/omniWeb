import pytest
from backend.core.skill_engine.skill_detector import skill_detector
from backend.core.skill_engine.skill_profile_builder import skill_profile_builder
from backend.core.opportunity_engine.opportunity_matcher import opportunity_matcher
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_skill_discovery():
    user_id = "test_user_discovery"
    # complex input
    skill_detector.detect_from_input(user_id, "The system architecture requires logical optimization of the engine.")
    
    profile = skill_profile_builder.get_profile(user_id)
    assert "systems_thinking" in profile.cognitive_metrics
    assert profile.cognitive_metrics["systems_thinking"].score > 0

def test_opportunity_matching():
    user_skills = ["thermodynamics", "programming"]
    matches = opportunity_matcher.find_matches(user_skills)
    
    assert len(matches) > 0
    # verify match for specific skill
    titles = [m.title for m in matches]
    assert any("Thermodynamics" in t for t in titles)
    assert any("Programming" in t for t in titles)

def test_career_suggestion():
    # User has no skills, should suggest trending ones
    matches = opportunity_matcher.find_matches([])
    assert len(matches) > 0
    assert any(m.type == "career_path" for m in matches)
