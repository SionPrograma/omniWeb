import pytest
from backend.core.knowledge_domains.domain_registry import domain_registry
from backend.core.knowledge_domains.domain_models import DomainCategory

def test_domain_registry_initialization():
    domains = domain_registry.list_domains()
    assert len(domains) == 8
    
    categories = [d.category for d in domains]
    assert DomainCategory.SCIENCE in categories
    assert DomainCategory.PHILOSOPHY in categories

def test_get_domain():
    science = domain_registry.get_domain("science")
    assert science is not None
    assert science.name == "Science"
    assert science.category == DomainCategory.SCIENCE

def test_invalid_domain():
    ghost = domain_registry.get_domain("ghost_domain")
    assert ghost is None
