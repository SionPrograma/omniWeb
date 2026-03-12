from typing import List, Optional
from .logbook_models import Logbook, AffinitySignal, ConnectionType
from .logbook_manager import logbook_manager

class AffinityEngine:
    def calculate_affinity(self, logbook_a: Logbook, logbook_b: Logbook) -> Optional[AffinitySignal]:
        if logbook_a.id == logbook_b.id:
            return None
            
        # Semantic intersection of topics
        topics_a = set(logbook_a.knowledge_topics)
        topics_b = set(logbook_b.knowledge_topics)
        matching_topics = list(topics_a.intersection(topics_b))
        
        # Project intersection
        projects_a = set(logbook_a.active_projects)
        projects_b = set(logbook_b.active_projects)
        matching_projects = list(projects_a.intersection(projects_b))
        
        # Skill complementarity or similarity (simplified)
        skills_a = set(logbook_a.skills.keys())
        skills_b = set(logbook_b.skills.keys())
        matching_skills = skills_a.intersection(skills_b)
        
        # Calculate score
        topic_score = len(matching_topics) * 0.2
        project_score = len(matching_projects) * 0.5
        skill_score = len(matching_skills) * 0.1
        
        total_score = min(1.0, topic_score + project_score + skill_score)
        
        if total_score > 0.3:
            # Determine suggested connection type
            conn_type = ConnectionType.CONVERSATION
            if len(matching_projects) > 0:
                conn_type = ConnectionType.COLLABORATION
            elif len(matching_topics) > 3:
                conn_type = ConnectionType.RESEARCH_GROUP
                
            return AffinitySignal(
                source_logbook_id=logbook_a.id,
                target_logbook_id=logbook_b.id,
                score=total_score,
                matching_topics=matching_topics,
                matching_projects=matching_projects,
                suggested_connection_type=conn_type
            )
        
        return None

    def find_suggestions(self, owner_id: str) -> List[AffinitySignal]:
        my_logbook = logbook_manager.get_or_create_logbook(owner_id)
        suggestions = []
        
        for other_lb in logbook_manager.logbooks.values():
            signal = self.calculate_affinity(my_logbook, other_lb)
            if signal:
                suggestions.append(signal)
                
        # Sort by score descending
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions

affinity_engine = AffinityEngine()
