import pytest
from backend.core.knowledge_economy.skill_market_engine import skill_market_engine
from backend.core.knowledge_economy.project_matcher import project_matcher
from backend.core.knowledge_economy.economy_models import Opportunity
from backend.core.skill_engine.skill_models import SkillProfile
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_market_scarcity():
    scarcity = skill_market_engine.get_scarcity_index(["ai_orchestration"])
    assert scarcity > 0.9

def test_project_matching():
    profile = SkillProfile(
        user_id="test",
        top_skills=["ai_orchestration"]
    )
    pool = [Opportunity(title="AI Lead", type="job", description="Lead ai", required_skills=["ai_orchestration"])]
    matches = project_matcher.match(profile, pool)
    assert len(matches) == 1
    assert matches[0].title == "AI Lead"
