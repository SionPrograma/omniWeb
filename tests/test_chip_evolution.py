import pytest
from backend.core.self_evolving_factory.idea_cluster_analyzer import idea_cluster_analyzer
from backend.core.self_evolving_factory.automatic_chip_designer import automatic_chip_designer
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_idea_clustering():
    topics = ["physics", "physics", "physics", "math"]
    clusters = idea_cluster_analyzer.analyze_emergence(topics)
    assert len(clusters) == 1
    assert "Physics" in clusters[0].name

def test_automatic_design():
    topics = ["robotics", "robotics", "robotics"]
    clusters = idea_cluster_analyzer.analyze_emergence(topics)
    blueprint = automatic_chip_designer.design_from_cluster(clusters[0])
    assert "chip-advanced-robotics" in blueprint.name
