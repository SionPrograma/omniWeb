import uuid
import logging
from typing import List, Dict, Any
from .supercommand_models import SuperCommandIntent, SuperPrompt, ExecutionStep, TaskCategory, ExecutionStatus

logger = logging.getLogger(__name__)

class SuperPromptBuilder:
    """Converts a SuperCommandIntent into a structured SuperPrompt with multiple execution steps."""

    def build_prompt(self, intent: SuperCommandIntent) -> SuperPrompt:
        """Constructs a SuperPrompt with a predefined sequence of steps based on the category."""
        task_id = str(uuid.uuid4())
        title = f"Task: {intent.category.value.capitalize()} - {intent.target or 'General'}"
        description = f"Executing a guided {intent.category.value} workflow for: '{intent.command}'"
        
        steps = []
        
        if intent.category == TaskCategory.OPTIMIZATION:
            steps = [
                ExecutionStep(id=1, name="Audit Subsystem", action=f"Audit current state of {intent.target}"),
                ExecutionStep(id=2, name="Analyze Inefficiencies", action="Detect performance bottlenecks"),
                ExecutionStep(id=3, name="Apply Refactorings", action="Implement optimization patches"),
                ExecutionStep(id=4, name="Regression Test", action="Verify no side-effects"),
                ExecutionStep(id=5, name="Final Stability Check", action="Ensure system is verified stable")
            ]
        elif intent.category == TaskCategory.LEARNING:
            steps = [
                ExecutionStep(id=1, name="Search Knowledge", action=f"Retrieve semantic nodes for {intent.target}"),
                ExecutionStep(id=2, name="Generate Path", action="Create pedagogical structure"),
                ExecutionStep(id=3, name="Explain Concept", action="Provide structured explanation"),
                ExecutionStep(id=4, name="Identify Gaps", action="Check for missing prerequisites"),
                ExecutionStep(id=5, name="Update Knowledge Graph", action="Save new learnings")
            ]
        elif intent.category == TaskCategory.EXPLORATION:
            steps = [
                ExecutionStep(id=1, name="Init Exploration", action=f"Initialize discovery for {intent.target}"),
                ExecutionStep(id=2, name="Trace Connections", action="Identify related entities"),
                ExecutionStep(id=3, name="Semantic Mapping", action="Generate cluster map"),
                ExecutionStep(id=4, name="Export Graph Snippet", action="Capture relevant graph portion")
            ]
        elif intent.category == TaskCategory.ARCHITECTURE:
            steps = [
                ExecutionStep(id=1, name="Audit Architecture", action=f"Analyze code structure of {intent.target}"),
                ExecutionStep(id=2, name="Identify Vulnerabilities", action="Check security and decoupling"),
                ExecutionStep(id=3, name="Propose Improvements", action="Generate structural enhancements")
            ]
        elif intent.category == TaskCategory.SIMULATION:
            steps = [
                ExecutionStep(id=1, name="Define Environment", action=f"Gather parameters for {intent.target}"),
                ExecutionStep(id=2, name="Init Runtime Context", action="Bootstrapping simulation environment"),
                ExecutionStep(id=3, name="Run Engine Cycles", action="Simulate logic and iterations"),
                ExecutionStep(id=4, name="Report Outcome", action="Summarize results and patterns")
            ]
        else: # General
            steps = [
                ExecutionStep(id=1, name="Baseline Audit", action="System check"),
                ExecutionStep(id=2, name="Standard Execution", action=f"Fulfilling request: {intent.command}"),
                ExecutionStep(id=3, name="Final Verification", action="Stability audit")
            ]

        return SuperPrompt(
            task_id=task_id,
            title=title,
            category=intent.category,
            description=description,
            steps=steps
        )

superprompt_builder = SuperPromptBuilder()
