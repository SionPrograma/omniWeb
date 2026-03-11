import pytest
import sqlite3
from backend.core.knowledge_graph.graph_store import GraphStore
from backend.core.knowledge_graph.graph_models import KnowledgeNode, KnowledgeEdge
from backend.core.knowledge_graph.concept_extractor import ConceptExtractor
from backend.core.knowledge_graph.graph_query import GraphQueryEngine
from backend.core.knowledge_graph.graph_builder import GraphBuilder

from backend.core.permissions import set_chip_context

@pytest.fixture
def graph_store():
    return GraphStore()

@pytest.fixture
def extractor():
    return ConceptExtractor()

def test_save_and_retrieve_node(graph_store):
    with set_chip_context("core"):
        node = KnowledgeNode(
            node_type="topic",
            name="test_topic",
            description="Testing unit"
        )
        node_id = graph_store.save_node(node)
        assert node_id > 0
        
        retrieved = graph_store.get_node(node_id)
        assert retrieved.name == "test_topic"
        assert retrieved.node_type == "topic"

def test_concept_extraction(extractor):
    text = "The quick brown fox jumps over the lazy dog."
    concepts = extractor.extract_concepts(text)
    assert len(concepts) > 0
    # Common words like 'fox', 'dog' should be there and not 'the', 'over'
    concept_names = [c["name"] for c in concepts]
    assert "fox" in concept_names
    assert "the" not in concept_names

def test_edge_creation(graph_store):
    with set_chip_context("core"):
        n1 = KnowledgeNode(node_type="concept", name="A")
        n2 = KnowledgeNode(node_type="concept", name="B")
        
        id1 = graph_store.save_node(n1)
        id2 = graph_store.save_node(n2)
        
        edge = KnowledgeEdge(
            source_node=id1,
            target_node=id2,
            relationship="RELATES_TO",
            weight=0.8
        )
        edge_id = graph_store.save_edge(edge)
        assert edge_id > 0
        
        neighbors = graph_store.get_neighbors(id1)
        assert len(neighbors) > 0
        assert neighbors[0]["neighbor_name"] == "B"

def test_query_engine(graph_store):
    with set_chip_context("core"):
        query_engine = GraphQueryEngine()
        # Assuming 'test_topic' was created in previous test or create it here
        node = KnowledgeNode(node_type="topic", name="physics")
        nid = graph_store.save_node(node)
        
        node2 = KnowledgeNode(node_type="topic", name="gravity")
        nid2 = graph_store.save_node(node2)
        
        graph_store.save_edge(KnowledgeEdge(source_node=nid, target_node=nid2, relationship="RELATES_TO"))
        
        related = query_engine.get_related_topics("physics")
        assert any(r["name"] == "gravity" for r in related)

def test_graph_builder_integration(graph_store):
    with set_chip_context("core"):
        # This test might be heavier if it needs real memories
        # We can at least test it runs without error if database is set up
        builder = GraphBuilder()
        # We don't necessarily need memories in the DB to test the call,
        # but the logic for process_single_memory can be tested with a mock-like object
        class MockMemory:
            def __init__(self):
                self.title = "Test Memory"
                self.summary = "Testing the graph builder with meaningful concepts like combustion"
                self.source_chip = "test-chip"
                self.memory_type = "test"
                
        builder.process_single_memory(MockMemory())
        
        # Verify 'combustion' node was created
        node = graph_store.find_node_by_name("combustion")
        assert node is not None
        assert node.node_type == "topic"
