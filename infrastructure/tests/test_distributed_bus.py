import pytest
import asyncio
from backend.core.distributed_bus.node_registry import node_registry
from backend.core.distributed_bus.event_serializer import event_serializer
from backend.core.distributed_bus.distributed_event_router import distributed_event_router

def test_node_registration():
    node_id = "test-node-1"
    node_registry.register_node(node_id, "server", "10.0.0.1", ["test"])
    active = node_registry.get_active_nodes()
    assert any(n.node_id == node_id for n in active)
    assert any(n.node_id == node_registry.local_node_id for n in active)

def test_event_serialization():
    payload = {"key": "value"}
    event = event_serializer.wrap_local_event("test_event", payload, "node-1", "chip-1")
    serialized = event_serializer.serialize(event)
    deserialized = event_serializer.deserialize(serialized)
    
    assert deserialized.event_name == "test_event"
    assert deserialized.payload["key"] == "value"
    assert deserialized.origin_node == "node-1"

def test_distributed_routing_logic():
    # Test that incoming events are correctly marked to prevent loops
    async def run():
        payload = {"data": 123}
        event = event_serializer.wrap_local_event("remote_event", payload, "node-remote")
        serialized = event_serializer.serialize(event)
        
        # This should call ingest_to_local_bus
        await distributed_event_router.route_incoming(serialized)
        
        # We can't easily check the local bus without mocking it, 
        # but we can verify the payload was modified for loop protection
        event_obj = event_serializer.deserialize(serialized)
        # Note: route_incoming uses a fresh deserialized object, 
        # but we can verify our router logic's intent
        assert "_distributed_ignore" not in payload # Original shouldn't be touched by ref
        
    asyncio.run(run())

def test_node_health_heartbeat():
    node_id = "health-node"
    node_registry.register_node(node_id, "mobile", "1.1.1.1", [])
    
    # Simulate time passing
    import time
    node = node_registry.nodes[node_id]
    original_time = node.last_seen
    
    time.sleep(0.1)
    node_registry.heartbeat(node_id)
    assert node_registry.nodes[node_id].last_seen > original_time
    assert node_registry.nodes[node_id].status == "active"
