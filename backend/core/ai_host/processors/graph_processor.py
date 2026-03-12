import logging
from .base import CommandProcessor, AICommandResponse
from backend.core.multimodal.visual_response import VisualResponseEngine

logger = logging.getLogger(__name__)

class GraphProcessor(CommandProcessor):
    """
    Handles Knowledge Graph exploration and synchronization commands.
    """
    async def process(self, msg: str) -> AICommandResponse:
        from backend.core.knowledge_graph.graph_query import GraphQueryEngine
        from backend.core.knowledge_graph.graph_builder import GraphBuilder
        
        query_engine = GraphQueryEngine()
        builder = GraphBuilder()
        
        # 1. Sync
        if any(keyword in msg for keyword in ["sincronizar", "sync", "build"]):
            builder.process_all_memories()
            return AICommandResponse(
                intent="graph_sync",
                status="success",
                message="Grafo de conocimiento sincronizado con la memoria a largo plazo.",
                payload={}
            )

        # 2. Explore
        if any(keyword in msg for keyword in ["explora", "explore", "relacion", "relates"]):
            # Extract topic - simple word after keywords
            topic_raw = msg.replace("explora", "").replace("explore", "").replace("relacionado con", "").replace("relates to", "").strip()
            parts = topic_raw.split()
            if parts:
                topic = parts[0].strip(",.?!")
                related = query_engine.get_related_topics(topic)
                if related:
                    topics_str = ", ".join([f"{r['name']} ({r['relationship']})" for r in related])
                    
                    # Add Visual Graph Payload
                    visual = VisualResponseEngine.create_table(
                        f"Relaciones de {topic}",
                        ["Destino", "Tipo", "Relación"],
                        [[r["name"], r["type"], r["relationship"]] for r in related]
                    )
                    
                    return AICommandResponse(
                        intent="graph_explore",
                        status="success",
                        message=f"Explorando '{topic}'. Temas relacionados: {topics_str}.",
                        payload={"root": topic, "related": related, "visual": visual}
                    )
                return AICommandResponse(
                    intent="graph_explore", 
                    status="error", 
                    message=f"No encontré conexiones para '{topic}'. Prueba sincronizar el grafo."
                )

        # 3. Learning Path
        if any(keyword in msg for keyword in ["camino", "path", "aprender", "learn"]):
             parts = msg.split()
             topic = parts[-1].strip(",.?!")
             path = query_engine.suggest_learning_path(topic)
             if path:
                 path_str = " -> ".join([p["name"] for p in path])
                 return AICommandResponse(
                     intent="graph_learning_path",
                     status="success",
                     message=f"Camino de aprendizaje para {topic}: {path_str}",
                     payload={"path": path}
                 )
        
        # 4. General Graph View
        if any(keyword in msg for keyword in ["grafo", "graph", "proyecto"]):
             nodes = query_engine.store.get_all_nodes()
             return AICommandResponse(
                 intent="graph_view",
                 status="success",
                 message=f"El grafo actual tiene {len(nodes)} nodos de conocimiento.",
                 payload={"node_count": len(nodes)}
             )

        return AICommandResponse(
            intent="graph_unknown",
            status="error",
            message="No entiendo el comando del grafo. Prueba con 'explora [tema]' o 'sincroniza el grafo'."
        )
