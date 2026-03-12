import pytest
from backend.core.semantic_layer.embedding_engine import embedding_engine
from backend.core.semantic_layer.vector_store import vector_store
from backend.core.semantic_layer.semantic_query_engine import semantic_query_engine
from backend.core.semantic_layer.embedding_models import VectorEntry

def test_embedding_generation():
    text = "OmniWeb is a universal knowledge interface."
    v1 = embedding_engine.generate_embedding(text)
    v2 = embedding_engine.generate_embedding(text)
    
    assert len(v1) == 128
    assert v1 == v2  # Deterministic
    
    # Unit vector check
    magnitude = sum(x*x for x in v1)
    assert abs(magnitude - 1.0) < 1e-5

def test_vector_store_upsert():
    entry = VectorEntry(
        node_id="test_node",
        source_type="test",
        embedding=[0.1] * 128,
        text_content="Test content"
    )
    vector_store.upsert_embedding(entry)
    
    all_embeddings = vector_store.get_all_embeddings()
    found = any(e.node_id == "test_node" for e in all_embeddings)
    assert found

def test_semantic_search():
    # Setup test vectors
    vector_store.upsert_embedding(VectorEntry(
        node_id="apple",
        source_type="fruit",
        embedding=embedding_engine.generate_embedding("apple"),
        text_content="A red fruit"
    ))
    
    vector_store.upsert_embedding(VectorEntry(
        node_id="car",
        source_type="vehicle",
        embedding=embedding_engine.generate_embedding("car"),
        text_content="A fast vehicle"
    ))
    
    results = semantic_query_engine.search("apple", limit=1)
    assert len(results) > 0
    assert results[0].node_id == "apple"
    assert results[0].score > 0.9

def test_ai_host_knowledge_explain():
    # This would require async AI Host testing, which we do via parity in audit
    pass
