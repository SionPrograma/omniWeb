import logging
import json
import uuid
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class BranchRelation(BaseModel):
    relation_id: str
    branch_a_id: str
    branch_b_id: str
    relation_type: str  # COLLISION, REDUNDANCY, SYNERGY, DEPENDENCY
    affected_domains: List[str]
    confidence: float
    rationale: str
    risk_score: float = 0.0
    synergy_score: float = 0.0
    recommended_action: str

class CrossBranchEngine:
    """
    OMNIWEB — BLOQUE: CROSS-BRANCH SYNERGY ANALYSIS.
    Detects collisions, redundancies and synergies between tactical experiments.
    """

    def scan_active_branches(self) -> List[BranchRelation]:
        relations = []
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Fetch active branches
                branches = conn.execute("SELECT * FROM roadmap_branches WHERE branch_state = 'ACTIVE'").fetchall()
                if len(branches) < 2:
                    return []

                # 2. Extract metadata for all branches
                branch_data = {}
                for b in branches:
                    missions = conn.execute("SELECT * FROM mission_handoffs WHERE branch_id = ?", (b["branch_id"],)).fetchall()
                    surfaces = []
                    objectives = []
                    for m in missions:
                        surfaces.extend(json.loads(m["surface_affected"]) if m["surface_affected"] else [])
                        objectives.append(m["objective"])
                    
                    branch_data[b["branch_id"]] = {
                        "name": b["name"],
                        "surfaces": list(set(surfaces)),
                        "objectives": objectives,
                        "mission_count": len(missions)
                    }

                # 3. Pairwise Comparison
                b_ids = list(branch_data.keys())
                for i in range(len(b_ids)):
                    for j in range(i + 1, len(b_ids)):
                        rel = self._compare_branches(b_ids[i], b_ids[j], branch_data)
                        if rel:
                            relations.append(rel)
                
                # 4. Persistence (avoid duplicates)
                self._persist_relations(relations)
                
                # 5. Evaluate Consolidations (PHASE 105)
                self._evaluate_consolidations(relations)

        return relations

    def _compare_branches(self, id_a: str, id_b: str, data: Dict[str, Any]) -> Optional[BranchRelation]:
        a = data[id_a]
        b = data[id_b]

        # A. SURFACE OVERLAP
        shared_surfaces = list(set(a["surfaces"]) & set(b["surfaces"]))
        if not shared_surfaces:
            return None
            
        # Use min to detect when one is a subset of the other
        overlap_score = len(shared_surfaces) / min(len(a["surfaces"]), len(b["surfaces"]), 1)

        # B. OBJECTIVE SIMILARITY (Simple heuristic)
        obj_a = " ".join(a["objectives"]).lower()
        obj_b = " ".join(b["objectives"]).lower()
        
        # C. REDUNDANCY DETECTION
        if overlap_score > 0.6:
            # High surface overlap + similar keywords
            if self._has_redundancy(obj_a, obj_b):
                return BranchRelation(
                    relation_id=f"brel-{uuid.uuid4().hex[:6]}",
                    branch_a_id=id_a,
                    branch_b_id=id_b,
                    relation_type="REDUNDANCY",
                    affected_domains=shared_surfaces[:3],
                    confidence=0.85,
                    rationale=f"Las ramas '{a['name']}' y '{b['name']}' parecen perseguir objetivos equivalentes en dominios solapados.",
                    risk_score=0.2,
                    recommended_action="CONSOLIDAR en una única rama táctica."
                )

        # D. COLLISION DETECTION
        if overlap_score > 0.3:
            if self._detect_collision(obj_a, obj_b):
                return BranchRelation(
                    relation_id=f"brel-{uuid.uuid4().hex[:6]}",
                    branch_a_id=id_a,
                    branch_b_id=id_b,
                    relation_type="COLLISION",
                    affected_domains=shared_surfaces[:3],
                    confidence=0.9,
                    rationale=f"Conflicto de intención detectado: '{a['name']}' propone mutaciones contradictorias con '{b['name']}' en superficies compartidas.",
                    risk_score=0.8,
                    recommended_action="ARBITRAR PRIORIDAD o desglosar superficies."
                )

        # E. SYNERGY DETECTION
        if 0 < overlap_score < 0.3:
            # Different surfaces but same domain or complementary objectives
            if "refactor" in obj_a and "test" in obj_b:
                return BranchRelation(
                    relation_id=f"brel-{uuid.uuid4().hex[:6]}",
                    branch_a_id=id_a,
                    branch_b_id=id_b,
                    relation_type="SYNERGY",
                    affected_domains=shared_surfaces[:3] or list(set(a["surfaces"] + b["surfaces"])[:2]),
                    confidence=0.7,
                    rationale=f"Oportunidad de sinergia: '{a['name']}' sanea la estructura mientras '{b['name']}' expande la cobertura en zonas adyacentes.",
                    synergy_score=0.75,
                    recommended_action="COORDINAR MERGE para validar saneamiento con tests."
                )

        return None

    def _has_redundancy(self, text_a: str, text_b: str) -> bool:
        # Simple keyword overlap
        words_a = set(re.findall(r"\w+", text_a))
        words_b = set(re.findall(r"\w+", text_b))
        common = words_a & words_b
        return len(common) > 5 # heuristic threshold

    def _detect_collision(self, text_a: str, text_b: str) -> bool:
        # Look for conflicting verbs
        conflicts = [
            ("borrar", "actualizar"), ("borrar", "refactorizar"), ("borrar", "migrar"),
            ("eliminar", "refactorizar"), ("eliminar", "corregir"),
            ("reemplazar", "migrar"), ("reemplazar", "corregir")
        ]
        text_a, text_b = text_a.lower(), text_b.lower()
        for v1, v2 in conflicts:
            if (v1 in text_a and v2 in text_b) or (v2 in text_a and v1 in text_b):
                return True
        return False

    def _evaluate_consolidations(self, relations: List[BranchRelation]):
        proposals = []
        for r in relations:
            if r.relation_type == "REDUNDANCY" and r.confidence >= 0.8:
                # Strong redundancy candidate for consolidation
                proposals.append({
                    "id": f"cons-{uuid.uuid4().hex[:6]}",
                    "primary": r.branch_a_id,
                    "secondary": r.branch_b_id,
                    "ref_id": r.relation_id,
                    "type": "ABSORB",
                    "confidence": r.confidence,
                    "surfaces": r.affected_domains,
                    "rationale": f"Las ramas presentan un solapamiento táctico del {(r.confidence*100):.0f}%. " +
                                 "Consolidar evitará duplicar esfuerzos en la misma superficie crítica.",
                    "gain": f"Simplificación del roadmap al unificar {len(r.affected_domains)} superficies bajo un único criterio."
                })
        
        if proposals:
            self._persist_consolidations(proposals)

    def _persist_consolidations(self, proposals: List[Dict[str, Any]]):
        with db_manager.get_connection() as conn:
            for p in proposals:
                # Avoid duplicates: same branch pair already in PROPOSED/ACCEPTED state
                exists = conn.execute("""
                    SELECT 1 FROM branch_consolidations 
                    WHERE (primary_branch_id = ? AND secondary_branch_id = ?) 
                       OR (primary_branch_id = ? AND secondary_branch_id = ?)
                       AND state IN ('PROPOSED', 'ACCEPTED')
                """, (p["primary"], p["secondary"], p["secondary"], p["primary"])).fetchone()
                
                if not exists:
                    conn.execute("""
                        INSERT INTO branch_consolidations (
                            consolidation_id, primary_branch_id, secondary_branch_id,
                            relation_ref_id, consolidation_type, confidence,
                            shared_surfaces, rationale, expected_gain
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p["id"], p["primary"], p["secondary"], p["ref_id"],
                        p["type"], p["confidence"], json.dumps(p["surfaces"]),
                        p["rationale"], p["gain"]
                    ))
            conn.commit()

    def _persist_relations(self, relations: List[BranchRelation]):
        with db_manager.get_connection() as conn:
            for r in relations:
                # Upsert logic based on branch pair
                # Sort IDs to ensure canonical pair order
                sort_ids = sorted([r.branch_a_id, r.branch_b_id])
                a_id, b_id = sort_ids[0], sort_ids[1]
                
                conn.execute("""
                    INSERT INTO branch_synergy_relations (
                        relation_id, branch_a_id, branch_b_id, relation_type,
                        affected_domains, confidence, rationale, risk_score, 
                        synergy_score, recommended_action, status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', CURRENT_TIMESTAMP)
                    ON CONFLICT(relation_id) DO UPDATE SET
                        relation_type = excluded.relation_type,
                        confidence = excluded.confidence,
                        rationale = excluded.rationale,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    r.relation_id, a_id, b_id, r.relation_type,
                    json.dumps(r.affected_domains), r.confidence, r.rationale,
                    r.risk_score, r.synergy_score, r.recommended_action
                ))
            conn.commit()

branch_synergy_engine = CrossBranchEngine()
