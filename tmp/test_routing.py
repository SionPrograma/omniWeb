
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.ai_host.command_router import ai_command_router
from backend.core.ai_host.intent_classifier import intent_classifier
from backend.core.ai_host.utils import extract_idea_content, extract_memory_query

async def test():
    msg = "Omni, guardá esta idea: crear drones logísticos."
    print(f"Testing message: {msg}")
    print(f"Extracted content: '{extract_idea_content(msg)}'")
    
    intent = intent_classifier.classify(msg.lower())
    print(f"Classified intent: {intent}")
    
    response = await ai_command_router.route(msg)
    print(f"Router response message: {response.message}")
    
    msg3 = "Omni, buscá ideas sobre logística."
    print(f"\nTesting message: {msg3}")
    print(f"Extracted query: '{extract_memory_query(msg3)}'")
    intent3 = intent_classifier.classify(msg3.lower())
    print(f"Classified intent: {intent3}")
    response3 = await ai_command_router.route(msg3)
    print(f"Router response message:\n{response3.message}")

if __name__ == "__main__":
    asyncio.run(test())
