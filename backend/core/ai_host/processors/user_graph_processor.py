import logging
from typing import Dict, Any, Optional, List
from .base import CommandProcessor, AICommandResponse
from backend.core.user_graph.engine import user_graph_engine
from backend.core.user_graph.models import GraphNode

logger = logging.getLogger(__name__)

class UserGraphProcessor(CommandProcessor):
    """
    AI Host Processor for Personal Knowledge Graph Queries.
    Phase 18: User Semantic Memory Graph.
    """

    async def can_handle(self, command: str) -> bool:
        terms = ["relacionado con", "related to", "depende de", "depends on", "mi grafo", "my graph", "conexiones", "connections"]
        cmd = command.lower()
        return any(term in cmd for term in terms)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = command.lower()
        user_id = str(context.get("user_id", "1")) if context else "1"
        
        # 1. Full Graph Request
        if any(x in cmd for x in ["mostrar grafo", "ver conexiones", "show my graph"]):
             graph = user_graph_engine.get_user_graph(user_id)
             message = (
                 f"### 🕸️ Tu Grafo de Conocimiento Personal\n"
                 f"He mapeado **{len(graph.nodes)} nodos** y **{len(graph.edges)} relaciones** semánticas en tu memoria.\n\n"
                 f"Este grafo conecta tus ideas, tareas y eventos de forma automática."
             )
             return AICommandResponse(
                 intent="user_graph_summary",
                 status="success",
                 message=message,
                 payload={"nodes": len(graph.nodes), "edges": len(graph.edges)}
             )

        # 2. Relationship Query (e.g., "What is related to audio?")
        graph = user_graph_engine.get_user_graph(user_id)
        relevant_nodes = []
        for term in cmd.split():
            if len(term) > 3:
                for node in graph.nodes:
                    if term in node.content.lower():
                        relevant_nodes.append(node)
        
        relevant_nodes = list({n.id: n for n in relevant_nodes}.values()) # deduplicate
        
        if not relevant_nodes:
            return AICommandResponse(
                intent="user_graph_query",
                status="success",
                message="No encontré conexiones directas para ese tema en tu grafo de conocimiento."
            )

        # Find neighbors for the first found node
        neighbors = user_graph_engine.get_neighbors(user_id, relevant_nodes[0].id)
        
        rel_text = "\n".join([f"- **{n['relation_type']}**: {n['neighbor_content']}" for n in neighbors[:5]])
        message = (
            f"### 🔗 Conexiones Detectadas\n"
            f"El nodo '{relevant_nodes[0].content[:30]}...' tiene las siguientes relaciones:\n\n"
            f"{rel_text}"
        )

        return AICommandResponse(
            intent="user_graph_query",
            status="success",
            message=message,
            payload={"source": relevant_nodes[0].id, "neighbor_count": len(neighbors)}
        )
