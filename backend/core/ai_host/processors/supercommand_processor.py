import logging
import asyncio
from typing import Dict, Any, Optional
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse
from backend.core.supercommand.supercommand_parser import supercommand_parser
from backend.core.supercommand.superprompt_builder import superprompt_builder
from backend.core.supercommand.loop_executor import loop_executor
from backend.core.supercommand.result_summarizer import result_summarizer

logger = logging.getLogger(__name__)

class SuperCommandProcessor(CommandProcessor):
    """Handles complex multi-step task orchestrations via SuperCommand Engine."""

    async def can_handle(self, command: str) -> bool:
        """Determines if the command has high complexity or matches specific task patterns."""
        intent = supercommand_parser.parse(command)
        # We handle anything that matches our specialized task patterns
        return intent is not None and intent.complexity >= 0.3

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        """Parses, builds a prompt, and executes the supercommand through the Stability Loop."""
        # 1. Parse Intent
        intent = supercommand_parser.parse(command)
        if not intent:
            return AICommandResponse(message="Comando no reconocido para orquestación compleja.", intent="unknown")

        # 2. Build SuperPrompt
        prompt = superprompt_builder.build_prompt(intent)
        
        # 3. Execute through Loop
        # Note: In a real system, we'd probably spawn this as a background task and return a task_id
        # For this version, we execute synchronously for the user response.
        result = await loop_executor.execute(prompt)
        
        # 4. Summarize Outcome
        summary_text = result_summarizer.summarize(result)
        
        return AICommandResponse(
            status="success",
            message=summary_text,
            payload={
                "task_id": result.task_id,
                "status": "completed" if result.success else "failed",
                "summary": result.summary,
                "actions": result.actions_performed,
                "issues": result.issues_detected,
                "is_supercommand": True
            },
            intent=f"supercommand_{intent.category.value}",
            display_data={
                "task_title": prompt.title,
                "category": intent.category.value,
                "description": prompt.description,
                "success": result.success
            }
        )
