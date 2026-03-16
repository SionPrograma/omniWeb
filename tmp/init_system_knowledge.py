import sys
import os
import asyncio
import logging

# Set up paths
sys.path.append(os.getcwd())

# Mock logging for cleaner output
logging.basicConfig(level=logging.INFO)

async def init_shared_knowledge():
    from backend.core.ai_host.memory.knowledge_graph import knowledge_graph
    
    print("\n--- INITIALIZING SHARED KNOWLEDGE LAYER ---")
    
    # 1. System Overview
    Overview = knowledge_graph.store_knowledge_node(
        title="OmniWeb System Overview",
        content="OmniWeb is an AI Operating Environment composed of modular capabilities called 'chips'. The ecosystem is governed by an AI host named Omni, which coordinates reasoning, planning, and chip orchestration while continuously learning from runtime outcomes.",
        tags=["architecture", "overview", "omniweb"]
    )
    
    # 2. Component: AI Host
    AIHost = knowledge_graph.store_knowledge_node(
        title="AI Host (Omni)",
        content="The central reasoning entity responsible for interpreting user requests, generating technical hypotheses, creating task plans, and coordinating system actions through chips.",
        tags=["component", "reasoning", "host"]
    )
    
    # 3. Component: Cognitive Core
    CogCore = knowledge_graph.store_knowledge_node(
        title="Cognitive Core",
        content="Maintains the global world model of OmniWeb. Tracks system health, active chips, runtime evidence snapshots, active hypotheses, and execution history. It is the 'shared reality' for all AI components.",
        tags=["component", "state", "shared_core"]
    )
    
    # 4. Component: Evidence Engine
    EvEngine = knowledge_graph.store_knowledge_node(
        title="Evidence Engine",
        content="The data collection layer that gathers concrete runtime metrics, system state, and chip logs to ground AI reasoning in reality.",
        tags=["component", "evidence", "data"]
    )
    
    # 5. Component: Task Planner
    Planner = knowledge_graph.store_knowledge_node(
        title="Task Planner",
        content="Translates validated hypotheses into executable, safe, and modular step-by-step plans used by the Execution Controller.",
        tags=["component", "planning"]
    )
    
    # 6. Component: Execution Controller
    ExecController = knowledge_graph.store_knowledge_node(
        title="Execution Controller",
        content="Manages the execution of task plans. It runs steps sequentially, requests confirmation for high-risk actions, and records outcomes in the Cognitive Core and Adaptive Learning layers.",
        tags=["component", "execution"]
    )
    
    # 7. Component: Chip Orchestrator
    Orchestrator = knowledge_graph.store_knowledge_node(
        title="Chip Orchestrator",
        content="Coordinates the lifecycle and communication of individual Chips. Provides discovery, status tracking, and secure command routing.",
        tags=["component", "orchestration", "chips"]
    )
    
    # 8. Component: Adaptive Learning
    LearningLayer = knowledge_graph.store_knowledge_node(
        title="Adaptive Learning Layer",
        content="Self-improvement mechanism that analyzes execution outcomes (SUCCESS/FAILURE/PARTIAL). It recalibrates hypothesis confidence scores and extracts recurring system patterns to improve future decisions.",
        tags=["component", "learning", "improvement"]
    )
    
    # 9. Component: Creator Copilot
    Copilot = knowledge_graph.store_knowledge_node(
        title="Creator Copilot",
        content="Specialized AI interface that assists the human Creator in expanding the system, modifying code, and managing the architecture via Creator Mode.",
        tags=["component", "development", "creation"]
    )

    # 10. Chip Ecosystem
    ChipEcho = knowledge_graph.store_knowledge_node(
        title="Chip Ecosystem",
        content="The modular foundation of OmniWeb. Chips are independent units of capability (logistics, finance, dev tools, etc.) that must be discoverable, orchestratable, observable, and safe.",
        tags=["chips", "modular", "ecosystem"]
    )

    # 11. Creator Context
    CreatorContext = knowledge_graph.store_knowledge_node(
        title="Creator Context & Authority",
        content="The human Creator is the highest authority. The system aims to augment (not replace) human intelligence, automate complex workflows, and organize knowledge to support human creativity. Access is granted via Creator Mode.",
        tags=["creator", "philosophy", "authority"]
    )

    # 12. System Philosophy
    Philosophy = knowledge_graph.store_knowledge_node(
        title="OmniWeb Philosophy",
        content="Principles: 1. Augment Human Intelligence. 2. Evidence-Based Reasoning (grounded in metrics). 3. Continuous Learning. 4. Modular Evolution (Everything is a Chip). 5. Transparency (Explain logic and limitations).",
        tags=["philosophy", "principles"]
    )

    # 13. Reasoning Model
    ReasoningModel = knowledge_graph.store_knowledge_node(
        title="Standard Reasoning Cycle",
        content="The 'Omni Loop': Observe (Metrics/Evidence) -> Hypothesize (Reasoning) -> Plan (Sequencing) -> Execute (Action) -> Learn (Refinement).",
        tags=["reasoning", "loop", "logic"]
    )

    # 14. Memory Layers
    MemoryLayers = knowledge_graph.store_knowledge_node(
        title="OmniWeb Memory Architecture",
        content="Layers: 1. Runtime Memory (Short-term). 2. Cognitive Memory (Hypotheses/History). 3. Learning Memory (Confidence/Patterns). 4. Semantic Memory (Infrastructure Knowledge).",
        tags=["memory", "components"]
    )

    # 15. Long Term Vision
    Vision = knowledge_graph.store_knowledge_node(
        title="OmniWeb Long-Term Vision",
        content="Evolve into a fully self-improving AI operating environment that accelerates human innovation by building software ecosystems and organizing knowledge networks autonomously.",
        tags=["vision", "future"]
    )

    # LINK NODES
    # System -> Components
    ids = [Overview.id, AIHost.id, CogCore.id, EvEngine.id, Planner.id, ExecController.id, Orchestrator.id, LearningLayer.id, Copilot.id, ChipEcho.id, CreatorContext.id, Philosophy.id, ReasoningModel.id, MemoryLayers.id, Vision.id]
    
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            knowledge_graph.link_knowledge_nodes(ids[i], ids[j])

    print(f"\nSUCCESS: Knowledge Graph populated with {len(ids)} foundational nodes.")

if __name__ == "__main__":
    try:
        # We need to ensure DB exists or at least the manager is ready
        # In a real run, this would be part of host startup.
        asyncio.run(init_shared_knowledge())
    except Exception as e:
        print(f"FAILED TO INITIALIZE KNOWLEDGE: {e}")
