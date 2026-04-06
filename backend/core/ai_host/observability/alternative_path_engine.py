import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class AlternativePath(BaseModel):
    path_id: str
    branch_id: str
    path_type: str
    proposed_strategy: str
    expected_benefit: str
    expected_risk_reduction: float
    confidence: float
    rationale: str
    supporting_evidence: Dict[str, Any]
    suggested_scope_change: Optional[str]
    status: str = "PROPOSED"
    creator_action_required: bool = True
    created_at: str

class AlternativePathEngine:
    """
    OMNIWEB — BLOQUE: ALTERNATIVE PATH SUGGESTION ENGINE.
    Suggests safer or more efficient tactical routes based on historical evidence.
    """

    def generate_suggestions(self, branch_id: str) -> List[AlternativePath]:
        """
        Analyzes a branch and proposes alternative tactical paths if better precedents exist.
        """
        logger.info(f"Generating tactical alternatives for branch {branch_id}")
        
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Get Branch Info
                    branch = conn.execute("SELECT * FROM roadmap_branches WHERE branch_id = ?", (branch_id,)).fetchone()
                    if not branch: return []

                    # 2. Get Projections & Audit
                    roi = conn.execute("SELECT * FROM branch_predictive_roi_advisories WHERE branch_id = ? AND is_active = 1", (branch_id,)).fetchone()
                    
                    suggestions = []
                    
                    # 3. HEURISTIC: TOO BIG -> Suggest SPLIT
                    mission_count = conn.execute("SELECT COUNT(*) FROM mission_handoffs WHERE branch_id = ?", (branch_id,)).fetchone()[0]
                    if mission_count > 8:
                        suggestions.append(self._suggest_split(branch, mission_count))

                    # 4. HEURISTIC: PRECEDENT SEARCH
                    precedent = self._find_better_precedent(conn, branch)
                    if precedent:
                        suggestions.append(self._suggest_precedent(branch, precedent))

                    # 5. HEURISTIC: RELIEF FIRST
                    if roi and roi["predicted_return_band"] == "HIGH_RISK_LOW_RETURN":
                        suggestions.append(self._suggest_relief_first(branch, roi))

                    # 6. HEURISTIC: CONSOLIDATION
                    redundancy = conn.execute("""
                        SELECT * FROM branch_synergy_relations 
                        WHERE (branch_a_id = ? OR branch_b_id = ?) 
                        AND relation_type = 'REDUNDANCY' AND status = 'ACTIVE'
                    """, (branch_id, branch_id)).fetchone()
                    if redundancy:
                        suggestions.append(self._suggest_consolidation(branch, redundancy))

                    # 7. Persist & Return
                    for s in suggestions:
                        self._persist_suggestion(conn, s)
                    
                    conn.commit()
                    return suggestions

            except Exception as e:
                logger.error(f"Alternative path generation failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return []

    def _suggest_split(self, branch, count: int) -> AlternativePath:
        return AlternativePath(
            path_id=f"alt-split-{uuid.uuid4().hex[:6]}",
            branch_id=branch["branch_id"],
            path_type="SPLIT_INTO_SMALLER_BRANCHES",
            proposed_strategy="Dividir el objetivo actual en 2 o 3 mini-ramas incrementales.",
            expected_benefit="Reduce el radio de explosión, facilita rebases y acelera el merge de piezas sanas.",
            expected_risk_reduction=0.4,
            confidence=0.85,
            rationale=f"La rama tiene {count} misiones. Mantener branches de larga duración sin merge aumenta exponencialmente el riesgo de desincronización estructural.",
            supporting_evidence={"mission_count": count},
            suggested_scope_change="Extraer el 50% de las misiones a una nueva rama 'Phase 2'.",
            created_at=datetime.now().isoformat()
        )

    def _find_better_precedent(self, conn, branch) -> Optional[Dict[str, Any]]:
        # Fetch domains
        missions = conn.execute("SELECT surface_affected FROM mission_handoffs WHERE branch_id = ?", (branch["branch_id"],)).fetchall()
        domains = []
        for m in missions:
            if m["surface_affected"]:
                try: domains.extend(json.loads(m["surface_affected"]))
                except: pass
        if not domains: return None

        # Search for a similar merged branch with high ROI
        precedent = conn.execute("""
            SELECT b.branch_id, b.name, a.value_score, a.cost_score, a.rationale
            FROM roadmap_branches b
            JOIN branch_investment_audits a ON b.branch_id = a.branch_id
            JOIN mission_handoffs m ON b.branch_id = m.branch_id
            WHERE b.branch_id != ? AND b.branch_state = 'MERGED'
            AND a.return_band = 'HIGH_VALUE_LOW_COST'
            AND m.surface_affected LIKE ?
            ORDER BY a.value_score DESC LIMIT 1
        """, (branch["branch_id"], f"%{domains[0]}%")).fetchone()
        
        return dict(precedent) if precedent else None

    def _suggest_precedent(self, branch, precedent) -> AlternativePath:
        return AlternativePath(
            path_id=f"alt-prec-{uuid.uuid4().hex[:6]}",
            branch_id=branch["branch_id"],
            path_type="FOLLOW_SUCCESSFUL_PRECEDENT",
            proposed_strategy=f"Emular la ruta táctica de la rama exitosa '{precedent['name']}'.",
            expected_benefit="Alta probabilidad de éxito estructural con costo táctico conocido y controlado.",
            expected_risk_reduction=0.6,
            confidence=0.75,
            rationale=f"La rama '{precedent['name']}' intervino dominios similares con un ROI excepcional ({precedent['value_score']}). Seguir su patrón de misiones reduce la incertidumbre.",
            supporting_evidence={"precedent_branch_id": precedent["branch_id"], "historical_rationale": precedent["rationale"]},
            suggested_scope_change=f"Limitar misiones a las superficies validadas en {precedent['name']}.",
            created_at=datetime.now().isoformat()
        )

    def _suggest_relief_first(self, branch, roi) -> AlternativePath:
        return AlternativePath(
            path_id=f"alt-rel-{uuid.uuid4().hex[:6]}",
            branch_id=branch["branch_id"],
            path_type="SWITCH_TO_RELIEF_FIRST",
            proposed_strategy="Postergar expansión y lanzar una Misión de Alivio (Relief) primero.",
            expected_benefit="Limpia la fricción estructural antes de construir, reduciendo desastres en el merge temprano.",
            expected_risk_reduction=0.8,
            confidence=0.9,
            rationale="El ROI predictivo detectó 'Alta Resistencia'. Intentar construir sobre cimientos inestables drenará energía sin garantizar valor.",
            supporting_evidence={"predictive_roi_band": roi["predicted_return_band"], "rationale": roi["rationale"]},
            suggested_scope_change="Convertir rama actual en rama de Refactor/Alivio.",
            created_at=datetime.now().isoformat()
        )

    def _suggest_consolidation(self, branch, redundancy) -> AlternativePath:
        other_id = redundancy["branch_b_id"] if redundancy["branch_a_id"] == branch["branch_id"] else redundancy["branch_a_id"]
        return AlternativePath(
            path_id=f"alt-cons-{uuid.uuid4().hex[:6]}",
            branch_id=branch["branch_id"],
            path_type="CONSOLIDATE_WITH_EXISTING",
            proposed_strategy=f"Fusionar esta exploración con la rama activa '{other_id}'.",
            expected_benefit="Elimina duplicación de esfuerzo y evita colisiones de diseño en dominios compartidos.",
            expected_risk_reduction=0.5,
            confidence=0.8,
            rationale="Se ha detectado redundancia estructural. Dos ramas explorando el mismo hotspot táctico en paralelo es costoso e ineficiente.",
            supporting_evidence={"redundancy_relation_id": redundancy["relation_id"], "other_branch_id": other_id},
            suggested_scope_change="Merge inmediato a la rama par.",
            created_at=datetime.now().isoformat()
        )

    def _persist_suggestion(self, conn, s: AlternativePath):
        # Disable old same-type ones for this branch
        conn.execute("UPDATE branch_alternative_paths SET status = 'POSTPONED' WHERE branch_id = ? AND path_type = ? AND status = 'PROPOSED'", (s.branch_id, s.path_type))
        
        conn.execute("""
            INSERT INTO branch_alternative_paths (
                path_id, branch_id, path_type, proposed_strategy, expected_benefit, 
                expected_risk_reduction, confidence, rationale, supporting_evidence, 
                suggested_scope_change, status, creator_action_required, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s.path_id, s.branch_id, s.path_type, s.proposed_strategy, s.expected_benefit,
            s.expected_risk_reduction, s.confidence, s.rationale, json.dumps(s.supporting_evidence),
            s.suggested_scope_change, s.status, 1 if s.creator_action_required else 0, s.created_at
        ))

    def get_suggestions(self, branch_id: Optional[str] = None) -> List[AlternativePath]:
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM branch_alternative_paths WHERE status = 'PROPOSED'"
                    params = []
                    if branch_id:
                        query += " AND branch_id = ?"
                        params.append(branch_id)
                    
                    rows = conn.execute(query, params).fetchall()
                    for r in rows:
                        results.append(AlternativePath(
                            path_id=r["path_id"],
                            branch_id=r["branch_id"],
                            path_type=r["path_type"],
                            proposed_strategy=r["proposed_strategy"],
                            expected_benefit=r["expected_benefit"],
                            expected_risk_reduction=r["expected_risk_reduction"],
                            confidence=r["confidence"],
                            rationale=r["rationale"],
                            supporting_evidence=json.loads(r["supporting_evidence"]),
                            suggested_scope_change=r["suggested_scope_change"],
                            status=r["status"],
                            creator_action_required=bool(r["creator_action_required"]),
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch suggestions: {e}")
        return results

alternative_path_engine = AlternativePathEngine()
