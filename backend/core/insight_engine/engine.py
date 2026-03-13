import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .models import ActionableInsight, InsightType, InsightSeverity
from backend.core.user_logbook.manager import logbook_manager
from backend.core.user_logbook.models import UserEntryType, UserLogbookEntry
from backend.core.system_state.engine import state_engine
from backend.core.user_graph.engine import user_graph_engine
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class InsightEngine:
    """
    Actionable Insight Engine (Phase 19).
    Transforms logs, state, and graphs into proactive suggestions.
    """

    def __init__(self):
        self._cache: Dict[str, List[ActionableInsight]] = {}

    async def analyze_user(self, user_id: str) -> List[ActionableInsight]:
        """
        Runs a full analysis for a specific user.
        """
        with set_chip_context("core"):
            insights = []
            
            # 1. Pattern Detection (Logbook Analysis)
            insights.extend(await self._detect_logbook_patterns(user_id))
            
            # 2. System Health Insights (State Analysis)
            insights.extend(await self._detect_system_complexities(user_id))
            
            # 3. Knowledge Graph Clusters
            insights.extend(await self._analyze_graph_density(user_id))
            
            self._cache[user_id] = insights
            return insights

    async def _detect_logbook_patterns(self, user_id: str) -> List[ActionableInsight]:
        """
        Detects recurring themes in ideas/notes.
        """
        recent_entries = logbook_manager.list_entries(user_id, limit=50)
        ideas = [e for e in recent_entries if e.entry_type == UserEntryType.IDEA]
        
        if len(ideas) < 3:
            return []

        # Simple keyword frequency analysis
        word_counts = {}
        for idea in ideas:
            words = idea.content.lower().split()
            for w in set(words):
                if len(w) > 4:
                    word_counts[w] = word_counts.get(w, []) + [idea.id]

        insights = []
        for word, entry_ids in word_counts.items():
            if len(entry_ids) >= 3:
                insights.append(ActionableInsight(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    type=InsightType.PATTERN,
                    severity=InsightSeverity.INFO,
                    title=f"Recurring Theme: {word.capitalize()}",
                    description=f"You have mentioned '{word}' in {len(entry_ids)} different ideas recently. Should we consolidate these into a new project or task?",
                    related_entries=entry_ids,
                    metadata={"keyword": word}
                ))
        
        return insights

    async def _detect_system_complexities(self, user_id: str) -> List[ActionableInsight]:
        """
        Analyzes system health for warnings.
        """
        state = await state_engine.get_state()
        insights = []
        
        # Check for error chips
        error_chips = [c for c in state.chips if c.status == "error"]
        if error_chips:
            insights.append(ActionableInsight(
                id=str(uuid.uuid4()),
                user_id=user_id,
                type=InsightType.HEALTH,
                severity=InsightSeverity.CRITICAL,
                title="System Instability Detected",
                description=f"There are {len(error_chips)} chips in error state ({', '.join([c.slug for c in error_chips])}). Automatic healing attempts might be failing.",
                metadata={"chips": [c.slug for c in error_chips]}
            ))

        # Check for many pending fixes
        if state.pending_fixes > 5:
            insights.append(ActionableInsight(
                id=str(uuid.uuid4()),
                user_id=user_id,
                type=InsightType.HEALTH,
                severity=InsightSeverity.WARNING,
                title="Fix Backlog Growing",
                description="The system has a significant number of pending AutoFixes. Review the Mission Control for details.",
                metadata={"fix_count": state.pending_fixes}
            ))

        return insights

    async def _analyze_graph_density(self, user_id: str) -> List[ActionableInsight]:
        """
        Uses the Knowledge Graph (Phase 18) to find busy nodes.
        """
        graph = user_graph_engine.get_user_graph(user_id)
        if not graph.nodes:
            return []

        # Find nodes with many edges
        edge_counts = {}
        for edge in graph.edges:
            edge_counts[edge.source_node] = edge_counts.get(edge.source_node, 0) + 1
            edge_counts[edge.target_node] = edge_counts.get(edge.target_node, 0) + 1

        insights = []
        for node_id, count in edge_counts.items():
            if count >= 4:
                # Find node content
                node = next((n for n in graph.nodes if n.id == node_id), None)
                if node:
                    insights.append(ActionableInsight(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        type=InsightType.SUGGESTION,
                        severity=InsightSeverity.INFO,
                        title=f"Central Concept Detected: {node.content[:20]}...",
                        description=f"This entry is semantically connected to {count} other memories. It appears to be a core pillar of your current focus.",
                        related_entries=[node.entry_id] if node.entry_id else []
                    ))
        
        return insights

    def get_cached_insights(self, user_id: str) -> List[ActionableInsight]:
        return self._cache.get(user_id, [])

insight_engine = InsightEngine()
