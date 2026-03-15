import logging
from .integration_registry import integration_registry
from .bridges import (
    knowledge_bridge,
    pipeline_bridge,
    communication_bridge,
    mentor_bridge,
    accessibility_bridge,
    music_learning_bridge,
    cluster_bridge,
    spatial_bridge,
    storage_bridge,
    governance_bridge
)

logger = logging.getLogger(__name__)

async def start_integration_layer():
    """Initializes and activates all domain bridges."""
    logger.info("Initializing OmniWeb System Integration Layer...")
    
    # Register Bridges
    integration_registry.register_bridge(knowledge_bridge)
    integration_registry.register_bridge(pipeline_bridge)
    integration_registry.register_bridge(communication_bridge)
    integration_registry.register_bridge(mentor_bridge)
    integration_registry.register_bridge(accessibility_bridge)
    integration_registry.register_bridge(music_learning_bridge)
    integration_registry.register_bridge(cluster_bridge)
    integration_registry.register_bridge(spatial_bridge)
    integration_registry.register_bridge(storage_bridge)
    integration_registry.register_bridge(governance_bridge)
    
    # Initialize all
    await integration_registry.initialize_all()
    logger.info("OmniWeb System Integration Layer is ACTIVE.")

async def stop_integration_layer():
    """Gracefully shuts down the integration layer."""
    await integration_registry.shutdown_all()
