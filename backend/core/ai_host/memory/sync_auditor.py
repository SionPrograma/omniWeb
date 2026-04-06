import uuid
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator

logger = logging.getLogger(__name__)

class CrossDomainRelation(BaseModel):
    relation_id: str
    domain_a: str
    domain_b: str
    relation_type: str # CONTRACT_DEPENDENCY, READINESS_IMPACT, SYNC_CANDIDATE, BLOCKER
    evidence_summary: str
    severity: str = "low" # low, medium, high, critical
    suggested_action: str
    related_missions: List[str] = [] # Handoff IDs
    confidence: float = 0.5

class SyncAuditor:
    """
    OMNIWEB — BLOQUE: CROSS-DOMAIN SYNC AUDITOR.
    Detects logical and readiness dependencies between domains.
    """
    
    def audit_cross_domain_sync(self) -> List[CrossDomainRelation]:
        relations = []
        
        # 1. Fetch current macro state
        roadmap = roadmap_aggregator.get_macro_roadmap()
        all_handoffs = handoff_manager.get_all(include_archived=True)
        
        # 2. Analyze Readiness Transitions & Side Effects
        # If Domain A had a push recently, and Domain B missions are now 'Blocked' or 'Needs Rebase'
        recent_pushes = []
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("""
                    SELECT push_id, roadmap_group_id, updated_at as timestamp 
                    FROM atomic_push_sessions 
                    WHERE state = 'COMPLETED' 
                    AND updated_at > datetime('now', '-24 hours')
                """).fetchall()
                recent_pushes = [dict(r) for r in rows]

        for push in recent_pushes:
            domain_a = push["roadmap_group_id"].replace("surface_", "")
            # Check other domains for 'Blocked' states
            for g in roadmap.groups:
                domain_b = g.group_id.replace("surface_", "")
                if domain_a == domain_b: continue
                
                # If domain B is 'Stalled' or has many blocked missions
                if g.readiness_state in ["STALLED", "GOVERNANCE_HELD"] and g.blocked_count > 0:
                    rid = hashlib.sha256(f"impact:{domain_a}:{domain_b}".encode()).hexdigest()[:12]
                    relations.append(CrossDomainRelation(
                        relation_id=rid,
                        domain_a=domain_a,
                        domain_b=domain_b,
                        relation_type="READINESS_IMPACT",
                        evidence_summary=f"El dominio '{domain_b}' muestra bloqueos tras el último empuje atómico en '{domain_a}'. Posible desincronización de estado.",
                        severity="medium",
                        suggested_action=f"Ejecutar REBASE táctico en '{domain_b}' para sincronizar con '{domain_a}'.",
                        confidence=0.7
                    ))

        # 3. Semantic Objective Dependencies
        # Keywords to match cross-domain logic
        for h_a in all_handoffs:
            if h_a.readiness_state in ["ARCHIVED", "ABORTED"]: continue
            surface_a = h_a.surface_affected[0] if h_a.surface_affected else "general"
            
            for h_b in all_handoffs:
                if h_a.handoff_id == h_b.handoff_id: continue
                if h_b.readiness_state in ["ARCHIVED", "ABORTED"]: continue
                surface_b = h_b.surface_affected[0] if h_b.surface_affected else "general"
                if surface_a == surface_b: continue
                
                # Detection: One mission mentions the other domain or its specific surfaces
                if surface_b in h_a.objective.lower() or surface_b in h_a.briefing_title.lower():
                    rid = hashlib.sha256(f"contract:{surface_a}:{surface_b}".encode()).hexdigest()[:12]
                    relations.append(CrossDomainRelation(
                        relation_id=rid,
                        domain_a=surface_a,
                        domain_b=surface_b,
                        relation_type="CONTRACT_DEPENDENCY",
                        evidence_summary=f"Misión en '{surface_a}' [ID: {h_a.handoff_id[:6]}] referencia explícitamente el dominio '{surface_b}'.",
                        severity="high",
                        suggested_action="Coordinar secuencia de lanzamiento: A requiere B (o viceversa).",
                        related_missions=[h_a.handoff_id, h_b.handoff_id],
                        confidence=0.9
                    ))

        # 4. Filter & Group (Anti-Noise)
        unique_rels = {}
        for r in relations:
            key = (r.domain_a, r.domain_b, r.relation_type)
            if key not in unique_rels or r.confidence > unique_rels[key].confidence:
                unique_rels[key] = r
                
        return list(unique_rels.values())

    def get_coordination_mission_suggestion(self, relation_id: str) -> Optional[Dict[str, Any]]:
        """Proposes a mirror or sync mission based on the relation."""
        rels = self.audit_cross_domain_sync()
        rel = next((r for r in rels if r.relation_id == relation_id), None)
        if not rel: return None
        
        return {
            "objective": f"Sincronizar contrato y flujo entre '{rel.domain_a}' y '{rel.domain_b}' para resolver la dependencia detectada.",
            "surface_affected": [rel.domain_a, rel.domain_b],
            "risk_level": "medium",
            "constraints": [f"Validar integridad en {rel.domain_b} antes de empuje final", "Preservar compatibilidad de API"]
        }

sync_auditor = SyncAuditor()
