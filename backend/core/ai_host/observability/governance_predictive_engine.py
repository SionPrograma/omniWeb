import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class PredictiveAdvisory(BaseModel):
    advisory_id: str
    target_domain: str
    predictive_state: str # WATCH_CLOSELY, HIGH_DRIFT_PROBABILITY, PREVENTIVE_ACTION_RECOMMENDED
    risk_projection: str
    supporting_signals: List[str]
    historical_patterns: List[str]
    confidence: float
    rationale: str
    recommended_action: str
    is_active: bool = True
    freshness: str
    created_at: str

class GovernancePredictiveEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE PREDICTIVE DRIFT ADVISOR.
    Anticipates structural degradation by correlating Heatmap nodes with Debt and Learning Surface.
    """

    async def scan_for_drift(self, domain: str) -> Dict[str, Any]:
        """
        CAPA 2: REAL-TIME DOMAIN DRIFT ANALYSIS.
        Utility for Mission Co-pilot enrichment.
        """
        with set_chip_context("core"):
            try:
                advisories = self.get_active_advisories(domain=domain)
                if advisories:
                    best = max(advisories, key=lambda a: a.confidence)
                    return {
                        "prob_score": 0.8 if best.predictive_state == "HIGH_DRIFT_PROBABILITY" else 0.5,
                        "confidence": best.confidence,
                        "rationale": best.rationale,
                        "antipattens": best.historical_patterns
                    }
                
                # Fallback: check historical hotspots if no active advisor
                with db_manager.get_connection() as conn:
                    learning = conn.execute("SELECT * FROM governance_learning_items WHERE target_domain = ? AND is_antipattern = 1 ORDER BY confidence DESC LIMIT 1", (domain,)).fetchone()
                    if learning:
                        return {
                            "prob_score": 0.45,
                            "confidence": learning["confidence"],
                            "rationale": f"Dominio con lecciones de antipatrón: {learning['lesson_summary']}",
                            "antipattens": [learning["learning_item_id"]]
                        }
            except Exception as e:
                logger.error(f"Domain drift scan failed: {e}")
        
        return {"prob_score": 0.0, "confidence": 0.0, "rationale": "Estable.", "antipattens": []}

    def scan_drift_signals(self) -> List[PredictiveAdvisory]:
        """
        Runs a global scan for predictive drift signals.
        """
        with set_chip_context("core"):
            try:
                advisories = []
                with db_manager.get_connection() as conn:
                    # 1. Antipattern Drift
                    advisories.extend(self._scan_antipattern_drift(conn))
                    
                    # 2. Debt-Pressure Drift (Using HeatmapEngine)
                    advisories.extend(self._scan_debt_pressure_drift(conn))
                    
                    # 3. Resistance Early Warning
                    advisories.extend(self._scan_resistance_drift(conn))
                    
                    # 4. Persistence
                    conn.execute("UPDATE governance_predictive_advisories SET is_active = 0")
                    for adv in advisories:
                        self._persist_advisory(conn, adv)
                    
                    conn.commit()
                    return advisories
            except Exception as e:
                logger.error(f"Failed drift scan: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return []

    def get_active_advisories(self, domain: Optional[str] = None) -> List[PredictiveAdvisory]:
        results = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM governance_predictive_advisories WHERE is_active = 1"
                    if domain: query += f" AND target_domain = '{domain}'"
                    
                    rows = conn.execute(query).fetchall()
                    for r in rows:
                        results.append(PredictiveAdvisory(
                            advisory_id=r["advisory_id"],
                            target_domain=r["target_domain"],
                            predictive_state=r["predictive_state"],
                            risk_projection=r["risk_projection"],
                            supporting_signals=json.loads(r["supporting_signals"]),
                            historical_patterns=json.loads(r["historical_patterns"]),
                            confidence=r["confidence"],
                            rationale=r["rationale"],
                            recommended_action=r["recommended_action"],
                            is_active=bool(r["is_active"]),
                            freshness=r["freshness"],
                            created_at=r["created_at"]
                        ))
            except: pass
        return results

    def _scan_antipattern_drift(self, conn) -> List[PredictiveAdvisory]:
        hits = []
        antipatterns = conn.execute("SELECT * FROM governance_learning_items WHERE is_antipattern = 1").fetchall()
        for ap in antipatterns:
            domain = ap["target_domain"]
            cutoff = (datetime.now() - timedelta(days=1)).isoformat()
            active_traces = conn.execute("SELECT creator_action FROM governance_action_traces WHERE target_domain = ? AND applied_at > ?", (domain, cutoff)).fetchall()
            for trace in active_traces:
                if trace["creator_action"] in ap["lesson_summary"]:
                    hits.append(PredictiveAdvisory(
                        advisory_id=f"PA-AP-{uuid.uuid4().hex[:6]}",
                        target_domain=domain,
                        predictive_state="PREVENTIVE_ACTION_RECOMMENDED",
                        risk_projection="Alta probabilidad de ineficacia operativa detectada.",
                        supporting_signals=[f"Acción '{trace['creator_action']}' en dominio con antipatrón."],
                        historical_patterns=[ap["learning_item_id"]],
                        confidence=ap["confidence"],
                        rationale=f"El dominio {domain} históricamente no responde bien a '{trace['creator_action']}'. Se espera degradación.",
                        recommended_action=f"Abortar táctica temporal. {ap['recommended_behavior']}",
                        freshness=datetime.now().isoformat(),
                        created_at=datetime.now().isoformat()
                    ))
        return hits

    def _scan_debt_pressure_drift(self, conn) -> List[PredictiveAdvisory]:
        hits = []
        from backend.core.ai_host.observability.governance_heatmap_engine import heatmap_engine
        # Skip evaluation to avoid recursive calls
        nodes = heatmap_engine.get_friction_heatmap(skip_evaluation=True)
        
        for node in nodes:
            # PHASE 111: Recalibratable threshold
            from backend.core.governance.feedback_engine import feedback_engine
            friction_threshold = feedback_engine.get_parameter_value('PREDICTIVE_DRIFT', 'FRICTION_THRESHOLD', 65.0)
            
            if node.friction_score > friction_threshold:
                # Check for active debt in this domain
                debt_count = conn.execute(
                    "SELECT COUNT(*) as cnt FROM governance_risk_overrides WHERE affected_domain = ? AND is_active = 1", 
                    (node.domain,)
                ).fetchone()["cnt"]
                
                if debt_count > 0:
                    hits.append(PredictiveAdvisory(
                        advisory_id=f"PA-DP-{uuid.uuid4().hex[:6]}",
                        target_domain=node.domain,
                        predictive_state="HIGH_DRIFT_PROBABILITY",
                        risk_projection="Inestabilidad estructural por acumulación de deuda bajo presión táctica.",
                        supporting_signals=[f"Fricción: {node.friction_score}%", f"Deuda activa: {debt_count} items"],
                        historical_patterns=["DEBT_PRESSURE_ESCALATION"],
                        confidence=0.85,
                        rationale=f"El dominio {node.domain} tiene {debt_count} deudas vivas conviviendo con fricción elevada.",
                        recommended_action="Revisar y cerrar deuda técnica crítica antes de la próxima misión.",
                        freshness=datetime.now().isoformat(),
                        created_at=datetime.now().isoformat()
                    ))
        return hits

    def _scan_resistance_drift(self, conn) -> List[PredictiveAdvisory]:
        hits = []
        # Branch Autopsies use 'affected_domains' (JSON)
        all_autopsies = conn.execute("""
            SELECT affected_domains, resistance_events 
            FROM governance_branch_autopsies 
            WHERE resistance_events != '[]' AND created_at > ?
        """, ((datetime.now() - timedelta(days=5)).isoformat(),)).fetchall()
        
        for r in all_autopsies:
            domains = json.loads(r["affected_domains"])
            for domain in domains:
                hits.append(PredictiveAdvisory(
                    advisory_id=f"PA-RS-{uuid.uuid4().hex[:6]}",
                    target_domain=domain,
                    predictive_state="WATCH_CLOSELY",
                    risk_projection="Efecto rebote estructural probable.",
                    supporting_signals=[f"Resistencia en autopsia reciente (Dominios: {domain})"],
                    historical_patterns=["STRUCTURAL_RECOIL"],
                    confidence=0.7,
                    rationale=f"Misiones anteriores en {domain} mostraron resistencia estructural significativa.",
                    recommended_action="No lanzar misiones paralelas. Esperar estabilización.",
                    freshness=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat()
                ))
        return hits

    def _persist_advisory(self, conn, adv: PredictiveAdvisory):
        conn.execute("""
            INSERT INTO governance_predictive_advisories (
                advisory_id, target_domain, predictive_state, risk_projection,
                supporting_signals, historical_patterns, confidence, rationale,
                recommended_action, is_active, freshness, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            adv.advisory_id, adv.target_domain, adv.predictive_state, adv.risk_projection,
            json.dumps(adv.supporting_signals), json.dumps(adv.historical_patterns),
            adv.confidence, adv.rationale, adv.recommended_action, 
            1 if adv.is_active else 0, adv.freshness, adv.created_at
        ))

predictive_engine = GovernancePredictiveEngine()
