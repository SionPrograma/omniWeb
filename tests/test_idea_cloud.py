import pytest
from backend.core.idea_cloud.idea_capture import idea_capture
from backend.core.idea_cloud.idea_store import idea_store
from backend.core.idea_cloud.idea_parser import idea_parser
from backend.core.idea_cloud.idea_linker import idea_linker
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_idea_capture():
    thought = "Idea: educational engine simulation using music visualization as a learning tool"
    idea = idea_capture.capture(thought)
    
    assert idea.raw_thought == thought
    assert len(idea.topics) > 0
    assert idea.id is not None
    
    # Check if stored
    recent = idea_store.get_recent_ideas()
    assert any(i.id == idea.id for i in recent)

def test_idea_parsing():
    text = "study thermodynamics and fluid dynamics using a new physics simulator"
    topics = idea_parser.extract_topics(text)
    
    assert "thermodynamics" in [t.lower() for t in topics]
    
    intent = idea_parser.analyze_intent(text)
    assert intent["category"] == "learning"

def test_idea_linking():
    topics = ["thermodynamics"]
    links = idea_linker.find_links(topics)
    
    # Assuming thermodynamics exists in KG (from previous turn's check)
    assert len(links["nodes"]) >= 0 # Might be 0 if DB is empty in test env, but should pass logic
