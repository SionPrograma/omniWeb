
import pytest
import sys
import os
import asyncio

# Add root to sys.path
sys.path.append(os.getcwd())

from backend.core.long_memory.experience_recorder import experience_recorder
from backend.core.long_memory.memory_retriever import memory_retriever
from backend.core.long_memory.knowledge_linker import knowledge_linker
from backend.core.long_memory.memory_store import memory_store

@pytest.mark.asyncio
async def test_memory_creation_and_retrieval():
    # 1. Record an experience
    memory_id = experience_recorder.record_experience(
        memory_type="learning_memory",
        title="Estudio de Motores",
        summary="El usuario analizó el motor de combustión en la simulación.",
        content="Detalles: Ciclo de 4 tiempos, admisión, compresión, combustión, escape.",
        importance=0.9
    )
    assert memory_id is not None
    assert memory_id != -1

    # 2. Link it to a chip
    knowledge_linker.link_to_chip(memory_id, "musica") # Just a test link

    # 3. Retrieve it
    memories = memory_retriever.find_relevant_memories("combustión")
    assert len(memories) > 0
    assert memories[0].title == "Estudio de Motores"

    # 4. Filter sensitive
    sensitive_id = experience_recorder.record_experience(
        memory_type="system_memory",
        title="Leak Test",
        summary="Testing privacy",
        content="My password is: secret123",
        importance=0.5
    )
    assert sensitive_id is None # Should be filtered

@pytest.mark.asyncio
async def test_ai_host_memory_integration():
    from backend.core.ai_host.command_router import ai_command_router
    
    # Record a project memory first
    experience_recorder.record_experience(
        memory_type="project_memory",
        title="Proyecto Alfa",
        summary="Desarrollo de plataforma educacional.",
        content="El usuario está construyendo un simulador de física.",
        importance=1.0
    )
    
    # Send a natural language command
    response = await ai_command_router.route("continuar mi proyecto")
    assert response.intent == "memory_recall"
    assert "Proyecto Alfa" in response.message

if __name__ == "__main__":
    # Manual execution helper
    async def run_manual():
        print("Running manual tests for Long Term Memory Engine...")
        try:
            await test_memory_creation_and_retrieval()
            print("PASS: test_memory_creation_and_retrieval")
            await test_ai_host_memory_integration()
            print("PASS: test_ai_host_memory_integration")
        except Exception as e:
            print(f"FAIL: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
    asyncio.run(run_manual())
