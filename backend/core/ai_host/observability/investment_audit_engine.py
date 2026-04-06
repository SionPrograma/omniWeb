import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class TacticalInvestmentEngine:
    """
    OMNIWEB — BLOQUE: TACTICAL INVESTMENT AUDIT.
    Evaluates branch ROI based on effort (missions) vs structural outcome (learnings, consolidations).
    """

    def audit_branches(self) -> List[Dict[str, Any]]:
        audits = []
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                branches = conn.execute("SELECT branch_id, name, created_at FROM roadmap_branches WHERE branch_state IN ('ACTIVE', 'MERGED')").fetchall()
                
                for b in branches:
                    audit = self._audit_branch(dict(b), conn)
                    if audit:
                        audits.append(audit)
                        self._persist_audit(audit, conn)
                
                conn.commit()
        return audits

    def _audit_branch(self, branch: Dict[str, Any], conn) -> Optional[Dict[str, Any]]:
        branch_id = branch["branch_id"]
        
        # 1. Gather COST Evidence
        missions = conn.execute("SELECT COUNT(*) as count FROM mission_handoffs WHERE branch_id = ?", (branch_id,)).fetchone()
        mission_count = missions["count"]
        
        # For now, we skip advisories if the table governance_advisories doesn't exist
        # We can check for governance_predictive_advisories or just use mission activity as cost base
        advisory_count = 0
        
        created_at = datetime.fromisoformat(branch["created_at"])
        duration_days = (datetime.now() - created_at).days + 1
        
        tactical_cost = (mission_count * 5) + (advisory_count * 10) + (duration_days * 2)
        cost_factors = {
            "missions": mission_count,
            "advisories": advisory_count,
            "duration": duration_days
        }

        # 2. Gather VALUE Evidence
        # Using the correct table name found in governance_autopsy_engine.py
        autopsy = conn.execute("SELECT * FROM governance_branch_autopsies WHERE branch_id = ?", (branch_id,)).fetchone()
        learning_gain = 0
        if autopsy:
            learnings = json.loads(autopsy["lessons_learned"]) if autopsy["lessons_learned"] else []
            learning_gain = len(learnings) * 15

        consolidations = conn.execute("""
            SELECT COUNT(*) as count FROM branch_consolidations 
            WHERE primary_branch_id = ? AND state = 'ACCEPTED'
        """, (branch_id,)).fetchone()
        consolidation_gain = consolidations["count"] * 25
        
        friction_relief = 10 if mission_count > 0 else 0 
        
        structural_value = learning_gain + consolidation_gain + friction_relief
        value_factors = {
            "learnings": learning_gain / 15 if learning_gain > 0 else 0,
            "consolidations": consolidations["count"],
            "friction_relief": friction_relief
        }

        # 3. Banding Logic
        band = "EXPERIMENTAL"
        rationale = "Inversión inicial en curso."
        rec = "Seguir invirtiendo para validar retorno."
        
        if tactical_cost > 0:
            roi = structural_value / tactical_cost
            if roi > 2.0:
                band = "HIGH_VALUE_LOW_COST"
                rationale = "Retorno estructural excepcional. La rama ha resuelto deuda o aportado aprendizaje con mínimo esfuerzo."
                rec = "PRIORIZAR MERGE."
            elif roi > 1.0:
                band = "HIGH_VALUE_HIGH_COST"
                rationale = "Inversión robusta y justificada. Rama compleja con impacto alto."
                rec = "Mantener inversión."
            elif roi < 0.3 and tactical_cost > 30:
                band = "LOW_VALUE_HIGH_COST"
                rationale = "Drenaje táctico detectado. Elevado costo con escaso alivio real."
                rec = "Cerrar o consolidar inmediatamente."
            elif learning_gain >= 15:
                band = "EXPERIMENTAL_BUT_REVEALING"
                rationale = "Alto valor cognitivo. Ha mapeado problemas estructurales profundos."
                rec = "Preservar como rama de aprendizaje."
        
        return {
            "audit_id": f"inv-{uuid.uuid4().hex[:6]}",
            "branch_id": branch_id,
            "cost_score": tactical_cost,
            "cost_factors": cost_factors,
            "value_score": structural_value,
            "value_factors": value_factors,
            "return_band": band,
            "rationale": rationale,
            "recommendation": rec,
            "confidence": 0.9
        }

    def _persist_audit(self, audit: Dict[str, Any], conn):
        # Ensure the row exists or update it for the given branch_id
        # We'll use branch_id as the key for the current investment status
        conn.execute("""
            INSERT INTO branch_investment_audits (
                audit_id, branch_id, cost_score, cost_factors, 
                value_score, value_factors, return_band, rationale, 
                recommendation, confidence, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(audit_id) DO UPDATE SET
                cost_score = excluded.cost_score,
                value_score = excluded.value_score,
                return_band = excluded.return_band,
                updated_at = CURRENT_TIMESTAMP
        """, (
            audit["audit_id"], audit["branch_id"], audit["cost_score"], json.dumps(audit["cost_factors"]),
            audit["value_score"], json.dumps(audit["value_factors"]), audit["return_band"],
            audit["rationale"], audit["recommendation"], audit["confidence"]
        ))

investment_audit_engine = TacticalInvestmentEngine()
