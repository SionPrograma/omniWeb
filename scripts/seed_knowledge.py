import asyncio
from backend.core.knowledge_graph.graph_store import graph_store
from backend.core.permissions import set_chip_context

from backend.core.knowledge_graph.graph_models import KnowledgeNode

async def populate_kg():
    print("Populating KG with 'Thermodynamics' node...")
    with set_chip_context("core"):
        node = KnowledgeNode(
            name="Thermodynamics",
            node_type="concept",
            description="The study of heat and energy.",
            metadata={"domain": "physics"}
        )
        graph_store.save_node(node)
    print("[DONE] Node saved. Embedding should be generated.")

if __name__ == "__main__":
    asyncio.run(populate_kg())
