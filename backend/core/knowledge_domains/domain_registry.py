from typing import List, Dict
from .domain_models import KnowledgeDomain, DomainCategory

class DomainRegistry:
    def __init__(self):
        self.domains: Dict[str, KnowledgeDomain] = {}
        self._initialize_default_domains()

    def _initialize_default_domains(self):
        defaults = [
            (DomainCategory.SCIENCE, "Scientific exploration and empirical research."),
            (DomainCategory.HISTORY, "Chronicles of human events and temporal analysis."),
            (DomainCategory.PHILOSOPHY, "Structural thought and existential inquiry."),
            (DomainCategory.RELIGION, "Spiritual systems and theological studies."),
            (DomainCategory.POLITICS, "Governance, power structures and social organization."),
            (DomainCategory.TECHNOLOGY, "Innovation, engineering and digital systems."),
            (DomainCategory.ART, "Creative expression and aesthetic analysis."),
            (DomainCategory.HUMAN_DEVELOPMENT, "Individual and collective growth and optimization.")
        ]
        for cat, desc in defaults:
            domain_id = cat.value.replace(" ", "_")
            self.domains[domain_id] = KnowledgeDomain(
                id=domain_id,
                name=cat.value.capitalize(),
                category=cat,
                description=desc
            )

    def register_domain(self, domain: KnowledgeDomain):
        self.domains[domain.id] = domain

    def get_domain(self, domain_id: str) -> KnowledgeDomain:
        return self.domains.get(domain_id)

    def list_domains(self) -> List[KnowledgeDomain]:
        return list(self.domains.values())

domain_registry = DomainRegistry()
