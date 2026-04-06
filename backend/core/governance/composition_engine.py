import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.governance.wisdom_reasoner import wisdom_reasoner, WisdomSuggestion
from backend.core.governance.draft_engine import draft_engine, MissionDraft

logger = logging.getLogger(__name__)

class ActionPackage(BaseModel):
    package_id: str
    package_type: str # RELIEF_ACTION, ROOT_AUDIT, SAFE_REFACTOR, PREVENTIVE_STABILIZATION, EXPERIMENTAL_GUARDED
    package_title: str
    composite_objective: str
    involved_nodes: List[str]
    mission_component: MissionDraft
    advisory_components: List[Dict[str, Any]]
    rationale: str
    confidence: float
    risk_level: str
    package_risk_notes: str
    creator_decision: str = "PENDING"
    created_at: datetime = datetime.now()

class WisdomActionBridge:
    """
    OMNIWEB — BLOQUE: WISDOM-TO-ACTION BRIDGE.
    Composer layer that takes multiple wisdom nodes and synthesizes a coherent action package.
    """
    
    def __init__(self):
        self.package_types = {
            "REUSABLE_TACTIC": "RELIEF_ACTION_PACKAGE",
            "CAUTIONARY_PATTERN": "PREVENTIVE_STABILIZATION_PACKAGE",
            "HIGH_RELEVANCE_WISDOM": "SAFE_REFACTOR_PACKAGE",
            "ROOT_CAUSE_FINDING": "ROOT_AUDIT_ACTION_PACKAGE",
            "EXPERIMENTAL_REFERENCE": "EXPERIMENTAL_GUARDED_PACKAGE"
        }

    def compose_from_suggestions(self, context: Dict[str, Any]) -> Optional[ActionPackage]:
        """
        Synthesizes a package from reasoner output.
        """
        suggestions = wisdom_reasoner.analyze_context(context)
        if not suggestions:
            return None

        # Sort by match score
        suggestions.sort(key=lambda x: x.match_score, reverse=True)
        primary = suggestions[0]
        
        # Only compose if we have enough confidence
        if primary.match_score < 0.6:
            logger.info("Primary suggestion score too low for package composition.")
            return None

        # Build Package
        p_id = f"PKG-{uuid.uuid4().hex[:8].upper()}"
        p_type = self.package_types.get(primary.reasoning_type, "TACTICAL_ACTION_PACKAGE")
        
        # Create Mission Draft from primary
        mission_draft = draft_engine.create_draft_from_suggestion(primary.model_dump(), context)
        
        # Look for supporting / cautionary pieces
        advisories = []
        involved_nodes = [primary.node_id]
        combined_rationale = [f"Primario: {primary.rationale}"]
        risk_level = mission_draft.risk_level
        
        for supp in suggestions[1:]:
            # If same domain or highly relevant, include as advisory/support
            if supp.match_score > 0.5:
                involved_nodes.append(supp.node_id)
                combined_rationale.append(f"Soporte: {supp.title} - {supp.rationale}")
                
                if supp.reasoning_type == "CAUTIONARY_PATTERN":
                    advisories.append({
                        "id": f"ADV-{uuid.uuid4().hex[:4]}",
                        "title": f"Precaución: {supp.title}",
                        "note": supp.recommended_use,
                        "source_node": supp.node_id
                    })
                    risk_level = "HIGH" # Elevate risk if cautionary pattern is involved
                
                # Merge constraints if any (Heuristic)
                if "No mutar" not in mission_draft.constraints:
                     mission_draft.constraints.append(f"Respetar límites de {supp.title}")

        pkg = ActionPackage(
            package_id=p_id,
            package_type=p_type,
            package_title=f"Paquete Táctico: {primary.title}",
            composite_objective=mission_draft.objective,
            involved_nodes=involved_nodes,
            mission_component=mission_draft,
            advisory_components=advisories,
            rationale=" | ".join(combined_rationale),
            confidence=primary.confidence,
            risk_level=risk_level,
            package_risk_notes=f"Basado en {len(involved_nodes)} nodos de sabiduría. Tipo: {p_type}."
        )
        
        self.persist_package(pkg)
        return pkg

    def persist_package(self, pkg: ActionPackage):
        with db_manager.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO governance_action_packages (
                        package_id, package_type, package_title, composite_objective,
                        involved_nodes_json, mission_draft_json, advisory_drafts_json,
                        rationale, confidence, risk_level, package_risk_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pkg.package_id, pkg.package_type, pkg.package_title, pkg.composite_objective,
                    json.dumps(pkg.involved_nodes), json.dumps(pkg.mission_component.model_dump()),
                    json.dumps(pkg.advisory_components), pkg.rationale,
                    pkg.confidence, pkg.risk_level, pkg.package_risk_notes
                ))
                conn.commit()
            except Exception as e:
                logger.error(f"Package persistence failed: {e}")

    def list_pending_packages(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_action_packages WHERE creator_decision = 'PENDING'").fetchall()
            return [dict(r) for r in rows]

    def process_decision(self, package_id: str, decision: str, options: Dict[str, Any] = None) -> bool:
        """
        Decision: APPROVED, REJECTED
        APPROVED: Converts drafts into real System Missions and Advisories.
        """
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM governance_action_packages WHERE package_id = ?", (package_id,)).fetchone()
            if not row or row["creator_decision"] != 'PENDING':
                return False
            
            if decision == 'REJECTED':
                conn.execute("UPDATE governance_action_packages SET creator_decision = 'REJECTED' WHERE package_id = ?", (package_id,))
                conn.commit()
                return True
            
            if decision == 'APPROVED':
                try:
                    # Parse components
                    mission_draft = json.loads(row["mission_draft_json"])
                    advisories = json.loads(row["advisory_drafts_json"] or "[]")
                    
                    # 1. Realize Mission
                    from backend.core.ai_host.memory.mission_manager import mission_manager
                    new_mission = mission_manager.create_mission(
                        goal=mission_draft["objective"],
                        source_draft_id=mission_draft["draft_id"]
                    )
                    realized_mission_id = new_mission.mission_id
                    
                    # 2. Realize Advisories
                    for adv in advisories:
                        adv_id = f"ADV-{uuid.uuid4().hex[:8].upper()}"
                        conn.execute("""
                            INSERT INTO governance_advisories (advisory_id, source_pattern_id, advisory_state)
                            VALUES (?, ?, ?)
                        """, (adv_id, adv["source_node"], "ACCEPTED"))

                    # Update Package Status
                    conn.execute("""
                        UPDATE governance_action_packages 
                        SET creator_decision = 'REALIZED', realized_mission_id = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE package_id = ?
                    """, (realized_mission_id, package_id))
                    conn.commit()
                    
                    logger.info(f"Action Package {package_id} REALIZED as mission {realized_mission_id}")
                    return True
                except Exception as e:
                    logger.error(f"Package realization failed: {e}")
                    return False
                
        return False

wisdom_action_bridge = WisdomActionBridge()
