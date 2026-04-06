import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class LearningItem(BaseModel):
    learning_item_id: str
    learning_type: str
    target_domain: str
    lesson_summary: str
    recommended_behavior: str
    confidence: float
    supporting_evidence: Dict[str, Any]
    is_antipattern: bool = False
    occurrence_count: int = 1
    freshness: str
    created_at: str

class GovernanceLearningEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE LEARNING SURFACE ENGINE.
    Consolidates structural learning from outcomes, autopsies, and resistance signals.
    """

    def refresh_learning_surface(self) -> List[LearningItem]:
        """
        Re-evaluates the entire governance history to build the Learning Surface.
        """
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Clear current surface (or update selectively)
                    conn.execute("DELETE FROM governance_learning_items")
                    
                    learnings = []
                    
                    # 2. Extract Learning: TACTICAL EFFECTIVENESS (from Action Traces)
                    trace_results = self._analyze_action_traces(conn)
                    learnings.extend(trace_results)
                    
                    # 3. Extract Learning: RECURRENT RESISTANCE (from Relief Proposals)
                    resistance_results = self._analyze_resistance_history(conn)
                    learnings.extend(resistance_results)
                    
                    # 4. Extract Learning: AUTOPSY SYNTHESIS (from Branch Autopsies)
                    autopsy_results = self._analyze_autopsy_patterns(conn)
                    learnings.extend(autopsy_results)
                    
                    # 5. Persist Learnings
                    for item in learnings:
                        self._persist_learning(conn, item)
                    
                    conn.commit()
                    return learnings
            except Exception as e:
                logger.error(f"Failed to refresh learning surface: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return []

    def get_learnings(self) -> List[LearningItem]:
        """Returns consolidated structural learnings."""
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM governance_learning_items ORDER BY confidence DESC").fetchall()
                    for r in rows:
                        results.append(LearningItem(
                            learning_item_id=r["learning_item_id"],
                            learning_type=r["learning_type"],
                            target_domain=r["target_domain"],
                            lesson_summary=r["lesson_summary"],
                            recommended_behavior=r["recommended_behavior"],
                            confidence=r["confidence"],
                            supporting_evidence=json.loads(r["supporting_evidence"]),
                            is_antipattern=bool(r["is_antipattern"]),
                            occurrence_count=r["occurrence_count"],
                            freshness=r["freshness"],
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch learnings: {e}")
        return results

    def _analyze_action_traces(self, conn) -> List[LearningItem]:
        """Detects which tactics work and which fail in specific contexts."""
        items = []
        # Group by domain and action to find patterns
        traces = conn.execute("""
            SELECT target_domain, creator_action, outcome_status, COUNT(*) as count, 
                   GROUP_CONCAT(trace_id) as ids
            FROM governance_action_traces 
            WHERE outcome_status != 'PENDING_OUTCOME'
            GROUP BY target_domain, creator_action, outcome_status
        """).fetchall()
        
        for row in traces:
            domain = row["target_domain"]
            action = row["creator_action"]
            outcome = row["outcome_status"]
            count = row["count"]
            trace_ids = row["ids"].split(",")
            
            # Use a threshold: 2+ occurrences for 'strong' learning
            if count >= 2:
                if outcome == "EFFECTIVE":
                    items.append(LearningItem(
                        learning_item_id=f"LI-T-EFF-{uuid.uuid4().hex[:4]}",
                        learning_type="TACTIC_EFFECTIVE_IN_CONTEXT",
                        target_domain=domain,
                        lesson_summary=f"Táctica '{action}' confirmada como efectiva en {domain}.",
                        recommended_behavior=f"Priorizar '{action}' ante riesgos similares en este dominio.",
                        confidence=min(0.9, 0.6 + (count * 0.1)),
                        supporting_evidence={"trace_ids": trace_ids},
                        is_antipattern=False,
                        occurrence_count=count,
                        freshness=datetime.now().isoformat(),
                        created_at=datetime.now().isoformat()
                    ))
                elif outcome in ["NO_EFFECT", "DEGRADED_AFTER_ACTION"]:
                    items.append(LearningItem(
                        learning_item_id=f"LI-T-INE-{uuid.uuid4().hex[:4]}",
                        learning_type="TACTIC_INEFFECTIVE_IN_CONTEXT",
                        target_domain=domain,
                        lesson_summary=f"Táctica '{action}' resulta insuficiente en {domain}. Riesgo persistente.",
                        recommended_behavior=f"Evitar '{action}' en {domain}. Escalar a auditoría de raíz si hay presión.",
                        confidence=min(0.95, 0.7 + (count * 0.1)),
                        supporting_evidence={"trace_ids": trace_ids},
                        is_antipattern=True,
                        occurrence_count=count,
                        freshness=datetime.now().isoformat(),
                        created_at=datetime.now().isoformat()
                    ))
        return items

    def _analyze_resistance_history(self, conn) -> List[LearningItem]:
        """Detects recurring structural resistance hotspots."""
        items = []
        resistant = conn.execute("""
            SELECT source_heatmap_node, COUNT(*) as fail_count, GROUP_CONCAT(proposal_id) as ids
            FROM governance_relief_proposals 
            WHERE relief_outcome IN ('RESISTANT_HOTSPOT', 'RELIEF_INEFFECTIVE')
            GROUP BY source_heatmap_node
        """).fetchall()
        
        for row in resistant:
            domain = row["source_heatmap_node"]
            fails = row["fail_count"]
            ids = row["ids"].split(",")
            
            if fails >= 2:
                items.append(LearningItem(
                    learning_item_id=f"LI-R-REC-{uuid.uuid4().hex[:4]}",
                    learning_type="DOMAIN_RECURRENT_RESISTANCE",
                    target_domain=domain,
                    lesson_summary=f"Patrón de resistencia recurrente en {domain}. El dominio ignora parches tácticos.",
                    recommended_behavior="Cesar parches tácticos. Bloquear nuevas misiones hasta realizar Refactor Estructural.",
                    confidence=0.85 if fails == 2 else 0.95,
                    supporting_evidence={"relief_proposals": ids},
                    is_antipattern=True,
                    occurrence_count=fails,
                    freshness=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat()
                ))
        return items

    def _analyze_autopsy_patterns(self, conn) -> List[LearningItem]:
        """Distills structural findings from branch autopsies."""
        items = []
        # Find autopsies with matching lessons/findings for same domain
        # (Simplified: look for repeated 'findings' or lessons across branches)
        autopsies = conn.execute("SELECT branch_id, affected_domains, lessons_learned, structural_findings FROM governance_branch_autopsies").fetchall()
        
        domain_insights = {}
        for r in autopsies:
            domains = json.loads(r["affected_domains"])
            findings = json.loads(r["structural_findings"])
            for d in domains:
                if d not in domain_insights: domain_insights[d] = []
                domain_insights[d].extend(findings)
        
        for domain, all_findings in domain_insights.items():
            # If we have 2+ autopsies mentioning findings for same domain
            if len(all_findings) >= 2:
                items.append(LearningItem(
                    learning_item_id=f"LI-A-SYN-{uuid.uuid4().hex[:4]}",
                    learning_type="AUTOPSY_CONFIRMED_PATTERN",
                    target_domain=domain,
                    lesson_summary=f"Patrón estructural confirmado vía autopsias en {domain}: {all_findings[0]}",
                    recommended_behavior="Validar raíz estructural del dominio antes del próximo ciclo de integración.",
                    confidence=min(0.9, 0.5 + (len(all_findings) * 0.15)),
                    supporting_evidence={"related_autopsies": "Cross-branch autopsy findings match in this domain."},
                    occurrence_count=len(all_findings),
                    freshness=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat()
                ))
        return items

    def _persist_learning(self, conn, item: LearningItem):
        conn.execute("""
            INSERT INTO governance_learning_items (
                learning_item_id, learning_type, target_domain, lesson_summary, 
                recommended_behavior, confidence, supporting_evidence, is_antipattern,
                occurrence_count, freshness, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.learning_item_id, item.learning_type, item.target_domain, 
            item.lesson_summary, item.recommended_behavior, item.confidence,
            json.dumps(item.supporting_evidence), 1 if item.is_antipattern else 0,
            item.occurrence_count, item.freshness, item.created_at
        ))

learning_engine = GovernanceLearningEngine()
