import pytest
import asyncio
from backend.core.distributed_network.node_registry import network_node_registry, KnowledgeSummary, NodeCapabilities
from backend.core.distributed_network.node_discovery import node_discovery

@pytest.mark.asyncio
async def test_node_registration():
    # Clear for testing
    network_node_registry.nodes = {}
    
    caps = NodeCapabilities(has_ai_host=True)
    summary = KnowledgeSummary(node_count=10, embedding_count=5)
    
    network_node_registry.register_node(
        node_id="test-node-1",
        node_url="http://test:8000",
        capabilities=caps,
        knowledge_summary=summary
    )
    
    active = network_node_registry.get_active_nodes()
    assert len(active) == 1
    assert active[0].node_id == "test-node-1"
    assert active[0].knowledge_summary.node_count == 10

@pytest.mark.asyncio
async def test_summary_generation():
    # This might require some data in DB, so we'll just test the call doesn't crash
    summary = await node_discovery._generate_local_summary()
    assert isinstance(summary, KnowledgeSummary)
    assert hasattr(summary, "node_count")

@pytest.mark.asyncio
async def test_heartbeat_handling():
    network_node_registry.nodes = {}
    payload = {
        "node_id": "remote-node",
        "node_url": "http://remote:8000",
        "capabilities": {"has_ai_host": True},
        "knowledge_summary": {"node_count": 55, "embedding_count": 12},
        "timestamp": 123456789
    }
    
    await node_discovery.handle_remote_heartbeat(payload)
    node = network_node_registry.get_node("remote-node")
    assert node is not None
    assert node.knowledge_summary.node_count == 55
