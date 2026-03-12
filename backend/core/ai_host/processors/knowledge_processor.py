import logging
from .base import CommandProcessor, AICommandResponse
from backend.core.multimodal.visual_response import VisualResponseEngine

logger = logging.getLogger(__name__)

class KnowledgeProcessor(CommandProcessor):
    """
    Handles Knowledge Dialogue Mode using Semantic Layer & KG.
    """
    async def process(self, msg: str) -> AICommandResponse:
        from backend.core.semantic_layer.semantic_query_engine import semantic_query_engine
        from backend.core.knowledge_graph.graph_query import GraphQueryEngine
        
        query_engine = GraphQueryEngine()
        
        # 1. Explain [Concept]
        if any(keyword in msg for keyword in ["explica", "explain", "que es", "what is"]):
            for keyword in ["explica", "explain", "que es", "what is"]:
                msg = msg.replace(keyword, "")
            concept = msg.strip(",.?! ")
            
            # Using specific threshold for mock engine
            results = semantic_query_engine.search(concept, limit=1, threshold=0.3)
            
            if results:
                res = results[0]
                return AICommandResponse(
                    intent="knowledge_explain",
                    status="success",
                    message=f"Explicación técnica: {res.text_content}. Este concepto está relacionado con {res.source_type}.",
                    payload={"concept": concept, "source": res.source_type, "score": res.score}
                )
            return AICommandResponse(
                intent="knowledge_explain", 
                status="error", 
                message=f"No tengo información detallada sobre '{concept}' en mi base semántica."
            )

        # 2. Path / Map
        if any(keyword in msg for keyword in ["mapa", "map", "camino", "path"]):
            target = msg.split()[-1].strip(",.?!")
            path = query_engine.suggest_learning_path(target)
            if path:
                steps = [p["name"] for p in path]
                visual = VisualResponseEngine.create_knowledge_map(f"Mapa de {target}", steps)
                return AICommandResponse(
                    intent="knowledge_map",
                    status="success",
                    message=f"He generado un mapa de conocimiento para {target}. Sigue este camino: {' -> '.join(steps)}",
                    payload={"steps": steps, "visual": visual}
                )
            return AICommandResponse(
                intent="knowledge_map",
                status="error",
                message=f"No pude generar un camino de aprendizaje para '{target}'."
            )

        # 3. Connect [A] with [B] (Semantic bridge - Placeholder for Phase T)
        if "connect" in msg or "conecta" in msg:
             return AICommandResponse(
                intent="knowledge_connect",
                status="partial",
                message="La capacidad de puente semántico se activará en la Fase T."
            )

        return AICommandResponse(
            intent="knowledge_unknown",
            status="error",
            message="Comando de conocimiento no reconocido. Prueba con 'explica [concepto]' o 'mapa de [tema]'"
        )
