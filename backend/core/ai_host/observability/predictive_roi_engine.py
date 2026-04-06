import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class PredictiveROIAdvisory(BaseModel):
    advisory_id: str
    branch_id: str
    predicted_return_band: str
    predicted_cost_band: str
    predicted_value_band: str
    confidence: float
    rationale: str
    supporting_evidence: Dict[str, Any]
    recommended_strategy: str
    is_active: bool = True
    created_at: str

class PredictiveROIEngine:
    """
    OMNIWEB — BLOQUE: PREDICTIVE ROI ADVISOR.
    Anticipates tactical returns by correlating draft branches with historical investment patterns.
    """

    def analyze_branch_prospect(self, branch_id: str) -> Optional[PredictiveROIAdvisory]:
        """
        Analyzes a new or growing branch to project its likely ROI.
        """
        logger.info(f"Analyzing ROI prospect for branch {branch_id}")
        
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Get Branch Data
                    branch_row = conn.execute("SELECT * FROM roadmap_branches WHERE branch_id = ?", (branch_id,)).fetchone()
                    if not branch_row:
                        return None
                    
                    branch_name = branch_row["name"]
                    
                    # 2. Extract Domains (from existing missions or draft objective)
                    missions = conn.execute("SELECT surface_affected FROM mission_handoffs WHERE branch_id = ?", (branch_id,)).fetchall()
                    target_domains = []
                    for m in missions:
                        if m["surface_affected"]:
                            try:
                                domains = json.loads(m["surface_affected"])
                                target_domains.extend(domains)
                            except: pass
                    
                    target_domains = list(set(target_domains))
                    
                    # 3. Find Similar Historical Branches
                    historical_evidence = self._gather_historical_evidence(conn, branch_name, target_domains, branch_id)
                    
                    # 4. Integrate Learnings
                    learnings = self._get_relevant_learnings(conn, target_domains)
                    
                    # 5. Synthesize Prediction
                    advisory = self._synthesize_prediction(branch_id, historical_evidence, learnings)
                    
                    # 6. Persist
                    self._persist_advisory(conn, advisory)
                    conn.commit()
                    
                    return advisory
            except Exception as e:
                logger.error(f"Predictive ROI analysis failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None

    def _gather_historical_evidence(self, conn, name: str, domains: List[str], current_id: str) -> List[Dict[str, Any]]:
        evidence = []
        
        # Search by Domain Overlap
        if domains:
            placeholders = ",".join(["?"] * len(domains))
            # We look for branches that had missions in these domains
            rows = conn.execute(f"""
                SELECT DISTINCT b.branch_id, b.name, a.return_band, au.final_branch_outcome
                FROM roadmap_branches b
                LEFT JOIN branch_investment_audits a ON b.branch_id = a.branch_id
                LEFT JOIN governance_branch_autopsies au ON b.branch_id = au.branch_id
                JOIN mission_handoffs m ON b.branch_id = m.branch_id
                WHERE b.branch_id != ? AND b.branch_state IN ('MERGED', 'DISCARDED')
                AND m.surface_affected LIKE ?
            """, (current_id, f"%{domains[0]}%")).fetchall() # Simple LIKE for domain
            
            for r in rows:
                evidence.append(dict(r))
                
        return evidence[:5] # Limit to top 5 evidence points

    def _get_relevant_learnings(self, conn, domains: List[str]) -> List[Dict[str, Any]]:
        if not domains: return []
        placeholders = ",".join(["?"] * len(domains))
        rows = conn.execute(f"SELECT * FROM governance_learning_items WHERE target_domain IN ({placeholders})", domains).fetchall()
        return [dict(r) for r in rows]

    def _synthesize_prediction(self, branch_id: str, history: List[Dict[str, Any]], learnings: List[Dict[str, Any]]) -> PredictiveROIAdvisory:
        band = "INSUFFICIENT_EVIDENCE"
        cost = "MEDIUM"
        val = "MEDIUM"
        confidence = 0.5
        rationale = "Sin precedentes claros en estos dominios."
        strategy = "Tratar como exploración controlada con scope acotado."
        
        antipattern_detected = any(l["is_antipattern"] for l in learnings)
        merged_count = len([h for h in history if h["final_branch_outcome"] == "MERGED"])
        discarded_count = len([h for h in history if h["final_branch_outcome"] == "DISCARDED"])
        high_val_count = len([h for h in history if h["return_band"] == "HIGH_VALUE_LOW_COST"])
        
        evidence_summary = {
            "branch_refs": [h["branch_id"] for h in history],
            "learning_refs": [l["learning_item_id"] for l in learnings],
            "historical_merged": merged_count,
            "historical_discarded": discarded_count
        }

        # PHASE 111: Recalibratable thresholds
        from backend.core.governance.feedback_engine import feedback_engine
        base_success_conf = feedback_engine.get_parameter_value('PREDICTIVE_ROI', 'SUCCESS_CONFIDENCE', 0.8)

        if antipattern_detected:
            band = "HIGH_RISK_LOW_RETURN"
            cost = "HIGH"
            val = "LOW"
            confidence = base_success_conf
            rationale = "Se han detectado antipatrones estructurales confirmados en los dominios afectados. Existe riesgo de resistencia estructural."
            strategy = "ACORTAR SCOPE. Validar alivio de fricción antes de expandir."
            
        elif high_val_count > 0:
            band = "HIGH_EXPECTED_VALUE"
            cost = "LOW"
            val = "HIGH"
            confidence = base_success_conf - 0.05
            rationale = "Patrón similar a ramas históricas de alto retorno y bajo costo en estos dominios."
            strategy = "PROSEGUIR INVERSIÓN. Alta probabilidad de merge exitoso."
            
        elif merged_count > discarded_count:
            band = "MODERATE_EXPECTED_VALUE"
            cost = "MEDIUM"
            val = "MEDIUM"
            confidence = 0.65
            rationale = "Dominios con historial de merges exitosos, aunque con costo táctico moderado."
            strategy = "Mantener inversión nominal con checkpoints semanales."
            
        elif discarded_count > 0:
            band = "HIGH_RISK_LOW_RETURN"
            cost = "HIGH"
            val = "LOW"
            confidence = 0.7
            rationale = "Historial de ramas descartadas o estancadas en estos dominios."
            strategy = "DIVIDIR RAMA. Atacar sub-objetivos pequeños para evitar drenaje."

        elif not history and not learnings:
            band = "EXPERIMENTAL_BUT_POTENTIALLY_REVEALING"
            cost = "MEDIUM"
            val = "HIGH"
            confidence = 0.4
            rationale = "Nuevo territorio táctico. Sin fricción previa conocida pero sin precedentes de valor."
            strategy = "Exploración libre con presupuesto de tiempo limitado (Timebox)."

        return PredictiveROIAdvisory(
            advisory_id=f"proi-{uuid.uuid4().hex[:6]}",
            branch_id=branch_id,
            predicted_return_band=band,
            predicted_cost_band=cost,
            predicted_value_band=val,
            confidence=confidence,
            rationale=rationale,
            supporting_evidence=evidence_summary,
            recommended_strategy=strategy,
            is_active=True,
            created_at=datetime.now().isoformat()
        )

    def _persist_advisory(self, conn, a: PredictiveROIAdvisory):
        # Desactivar anteriores para la misma rama
        conn.execute("UPDATE branch_predictive_roi_advisories SET is_active = 0 WHERE branch_id = ?", (a.branch_id,))
        
        conn.execute("""
            INSERT INTO branch_predictive_roi_advisories (
                advisory_id, branch_id, predicted_return_band, predicted_cost_band, 
                predicted_value_band, confidence, rationale, supporting_evidence, 
                recommended_strategy, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a.advisory_id, a.branch_id, a.predicted_return_band, a.predicted_cost_band,
            a.predicted_value_band, a.confidence, a.rationale, json.dumps(a.supporting_evidence),
            a.recommended_strategy, 1 if a.is_active else 0, a.created_at
        ))

    def get_projections(self, branch_id: Optional[str] = None) -> List[PredictiveROIAdvisory]:
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM branch_predictive_roi_advisories WHERE is_active = 1"
                    params = []
                    if branch_id:
                        query += " AND branch_id = ?"
                        params.append(branch_id)
                    
                    rows = conn.execute(query, params).fetchall()
                    for r in rows:
                        results.append(PredictiveROIAdvisory(
                            advisory_id=r["advisory_id"],
                            branch_id=r["branch_id"],
                            predicted_return_band=r["predicted_return_band"],
                            predicted_cost_band=r["predicted_cost_band"],
                            predicted_value_band=r["predicted_value_band"],
                            confidence=r["confidence"],
                            rationale=r["rationale"],
                            supporting_evidence=json.loads(r["supporting_evidence"]),
                            recommended_strategy=r["recommended_strategy"],
                            is_active=bool(r["is_active"]),
                            created_at=r["created_at"]
                        ))
            except Exception as e:
                logger.error(f"Failed to fetch ROI projections: {e}")
        return results

predictive_roi_engine = PredictiveROIEngine()
