import logging
import json
from .memory_models import MemoryEntry
from .memory_store import memory_store

logger = logging.getLogger(__name__)

class ExperienceRecorder:
    """
    Records meaningful system/user experiences into Long Term Memory.
    """
    def record_experience(self, memory_type: str, title: str, summary: str, content: str, source_chip: str = None, importance: float = 0.5):
        """
        Main entry point for recording an experience.
        """
        # Privacy check: filter sensitive content
        if self._is_sensitive(content):
            logger.warning(f"ExperienceRecorder: Blocking sensitive memory: {title}")
            return

        memory = MemoryEntry(
            memory_type=memory_type,
            title=title,
            summary=summary,
            content=content,
            source_chip=source_chip,
            importance_score=importance
        )
        
        memory_id = memory_store.save_memory(memory)
        if memory_id != -1:
            logger.info(f"ExperienceRecorder: Recorded new {memory_type}: {title}")
            return memory_id
        return None

    def _is_sensitive(self, content: str) -> bool:
        """
        Strictly filters for raw secrets or passwords.
        """
        sensitive_keywords = ["password", "secret", "token", "hash_", "$2b$", "key="]
        low_content = content.lower()
        return any(k in low_content for k in sensitive_keywords)

    def record_project_milestone(self, project_name: str, chips_used: list, summary: str):
        content = f"Project: {project_name}\nChips: {', '.join(chips_used)}\nDetails: {summary}"
        return self.record_experience(
            memory_type="project_memory",
            title=f"Project Update: {project_name}",
            summary=summary[:100],
            content=content,
            importance=0.8
        )

experience_recorder = ExperienceRecorder()
