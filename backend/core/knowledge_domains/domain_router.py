from fastapi import APIRouter, HTTPException
from .domain_registry import domain_registry
from .domain_summary_engine import domain_summary_engine
from .domain_models import KnowledgeDomain, DomainSummary

router = APIRouter()

@router.get("/")
async def list_domains():
    return domain_registry.list_domains()

@router.get("/{domain_id}")
async def get_domain(domain_id: str):
    domain = domain_registry.get_domain(domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain

@router.get("/{domain_id}/summary")
async def get_domain_summary(domain_id: str):
    return await domain_summary_engine.generate_summary(domain_id)
