import logging
import json
from typing import Dict, Any, List
from ..domain_bridge import DomainBridge
from ..event_bus import integration_bus
from backend.core.knowledge_graph.graph_store import graph_store
from backend.core.knowledge_graph.graph_models import KnowledgeNode, KnowledgeEdge

logger = logging.getLogger(__name__)

class KnowledgeBridge(DomainBridge):
    """
    Connects all OmniWeb domains to the central Knowledge Graph.
    Ensures every meaningful platform event leaves a semantic footprint.
    """
    def __init__(self):
        super().__init__("knowledge_bridge", ["knowledge_graph", "all"])

    async def initialize(self):
        # Subscribe to major cross-domain events
        integration_bus.subscribe_to_domain("skill_detected", self.on_skill_detected)
        integration_bus.subscribe_to_domain("music_analyzed", self.on_music_analyzed)
        integration_bus.subscribe_to_domain("opportunity_matched", self.on_opportunity_matched)
        integration_bus.subscribe_to_domain("communication_logged", self.on_communication_logged)
        logger.info("KnowledgeBridge: Online and listening to domain events.")

    async def shutdown(self):
        pass

    async def on_skill_detected(self, payload: Dict[str, Any]):
        user_id = payload.get("user_id", "anonymous")
        skill_name = payload.get("metric_name")
        score = payload.get("score")
        
        # Ensure User node exists
        user_node_id = graph_store.save_node(KnowledgeNode(
            node_type="user",
            name=user_id,
            description=f"OmniWeb User: {user_id}",
            importance_score=0.5
        ))
        
        # Ensure Skill node exists
        skill_node_id = graph_store.save_node(KnowledgeNode(
            node_type="skill",
            name=skill_name,
            description=f"Skill: {skill_name}",
            importance_score=score or 0.1
        ))
        
        # Link User to Skill
        graph_store.save_edge(KnowledgeEdge(
            source_node=user_node_id,
            target_node=skill_node_id,
            relationship="POSSESSES",
            weight=score or 0.1,
            metadata={"source": "skill_engine"}
        ))

    async def on_music_analyzed(self, payload: Dict[str, Any]):
        # Connect musical results to the KG
        result = payload.get("analysis_result", {})
        note = result.get("last_note")
        bpm = result.get("bpm")
        
        if note:
            node_id = graph_store.save_node(KnowledgeNode(
                node_type="musical_concept",
                name=note,
                description=f"Musical Note detected during practice.",
                importance_score=0.2
            ))
            # Could link to the user too if context allows

    async def on_opportunity_matched(self, payload: Dict[str, Any]):
        user_id = payload.get("user_id")
        opportunity_id = payload.get("opportunity_id")
        
        # Log matching event in KG
        logger.info(f"KnowledgeBridge: Linking Opportunity {opportunity_id} to User {user_id}")
        # Graph logic here...
        
    async def on_communication_logged(self, payload: Dict[str, Any]):
        # Extract concepts from communication and link them in KG
        pass

knowledge_bridge = KnowledgeBridge()
