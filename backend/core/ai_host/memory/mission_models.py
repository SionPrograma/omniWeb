import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# --- ENUMS ---

class MissionStatus(str, Enum):
    OPEN = "OPEN"           # Active mission (Ready to focus or Background ready)
    RUNNING = "RUNNING"     # Parallel executing in background
    PAUSED = "PAUSED"       # Human interrupted or switched context
    BLOCKED = "BLOCKED"     # Stuck on an issue or verification failure
    COMPLETED = "COMPLETED" # Mission objective reached
    FAILED = "FAILED"       # Critical error or goal unreachable
    
    # MISSION HIERARCHY & BRANCHING (Phase 21)
    ARCHIVED = "ARCHIVED"   # Hidden from active UI but preserved
    ROLLED_BACK = "ROLLED_BACK" # Reverted branch
    SUPERSEDED = "SUPERSEDED" # Replaced by a retry link
    SUSPENDED = "SUSPENDED" # Auto-paused by priority engine

# --- MODELS ---

class StrategicPostMortem(BaseModel):
    """
    CAPA 1 (PHASE 69): STRATEGIC KNOWLEDGE SYNTHESIS.
    Captures high-level lessons learned from the mission diagnostic cycle.
    """
    summary: str
    dominant_pattern: str
    best_action: str
    avg_roi: float
    reusable_lesson: str
    confidence: float

class MissionHandoff(BaseModel):
    """
    Structured deep summary of a mission for audit, continuity and handoff.
    """
    mission_id: str
    briefing_title: str = "Mission Executive Briefing"
    goal: str
    executive_summary: str
    key_decisions: List[str] = Field(default_factory=list) 
    technical_impact: str = "TDB" 
    timeline_milestones: List[str]
    governance_footprint: Dict[str, Any] 
    multimodal_evidence_refs: List[str]
    recovery_events: List[str]
    final_status: MissionStatus
    next_steps: List[str]
    post_mortem: Optional[StrategicPostMortem] = None # PHASE 69
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """Generates a professional executive briefing in Markdown."""
        md = f"# 📋 {self.briefing_title}\n\n"
        md += f"**Mission ID:** `{self.mission_id}` | **Status:** `{self.final_status.value}`\n"
        md += f"**Timestamp:** {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        md += f"## 🎯 Goal & Scope\n{self.goal}\n\n"
        md += f"## 📝 Executive Summary\n{self.executive_summary}\n\n"
        
        if self.post_mortem:
            pm = self.post_mortem
            md += "## 🧠 Strategic Post-Mortem & Lessons Learned\n"
            md += f"> **Patrón Detectado:** {pm.dominant_pattern}\n"
            md += f"> **Lección Reutilizable:** {pm.reusable_lesson}\n"
            md += f"> **Eficacia de Rescate:** ROI Promedio de {pm.avg_roi:.1f} en la acción '{pm.best_action}'.\n\n"
            md += f"{pm.summary}\n\n"

        if self.key_decisions:
            md += "## ⚖️ Key Decisions\n"
            for d in self.key_decisions:
                md += f"- {d}\n"
            md += "\n"
            
        md += f"## 🛠️ Technical Impact & Results\n{self.technical_impact}\n\n"
        
        md += "## 🛡️ Governance & Integrity\n"
        gov = self.governance_footprint
        md += f"- **Health Score:** {(gov.get('score', 1.0)*100):.0f}%\n"
        if self.recovery_events:
            md += "- **Recovery Events:**\n"
            for r in self.recovery_events:
                md += f"  - ⚠️ {r}\n"
        md += "\n"
        
        md += "## 🛣️ Timeline & Milestones\n"
        for m in self.timeline_milestones:
            md += f"- {m}\n"
        md += "\n"
        
        md += "## 🚀 Next Steps & Continuous Actions\n"
        for s in self.next_steps:
            md += f"- {s}\n"
        
        return md

class MissionCompactDigest(BaseModel):
    """
    High-density operational summary for fast context switching (Bloque 22).
    """
    mission_id: str
    goal_compact: str
    status_label: str
    active_constraints: List[str] = Field(default_factory=list)
    governance_score: float = 1.0 # 0.0 to 1.0
    latest_incident: Optional[str] = None
    next_step_hint: str = "Continuar ejecución"
    multimodal_summary: Optional[str] = None
    readiness: str = "READY"
    updated_at: datetime = Field(default_factory=datetime.now)

class MissionState(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    mission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active_goal: str
    status: MissionStatus = MissionStatus.OPEN
    plan_id: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    blocked_reasons: List[str] = Field(default_factory=list)
    related_targets: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context_snap: Dict[str, Any] = Field(default_factory=dict)
    telemetry_snap: Dict[str, Any] = Field(default_factory=dict)
    visual_context: Optional[Dict[str, Any]] = None
    multimodal_history: List[Dict[str, Any]] = Field(default_factory=list)
    source_draft_id: Optional[str] = None # Traceability to Atlas draft
    friction: float = 1.0 # 0.0 to 1.0 (Phase 115)
    preconditions_ok: int = 1 # 1 = OK, 0 = FAIL (Phase 115)
    
    # PHASE 82: Authority Session Persistence (Hardening)
    authority_session: Dict[str, Any] = Field(default_factory=dict)
    
    parent_id: Optional[str] = None
    child_ids: List[str] = Field(default_factory=list)
    dependency_ids: List[str] = Field(default_factory=list)
    
    # PHASE 80: Strategic Governance
    last_recovery: Optional[Dict[str, Any]] = None
    last_audit_report: Optional[Dict[str, Any]] = None
    
    updated_at: datetime = Field(default_factory=datetime.now)
    relation_type: Optional[str] = None
    
    retried_from: Optional[str] = None
    branched_from: Optional[str] = None
    last_focused_at: datetime = Field(default_factory=datetime.now)
    
    priority_score: float = 0.0
    priority_class: str = "NORMAL"
    readiness_state: str = "READY"
    compact_digest: Optional[MissionCompactDigest] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def get_active_multimodal_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.multimodal_history: return []
        high_signal = [
            h for h in self.multimodal_history 
            if h.get("relevance") in ["CRITICAL", "SIGNAL"] or h.get("event") == "GATE_DECISION"
        ]
        latest_capture = next((h for h in reversed(self.multimodal_history) if h.get("event") in ["INITIAL_CAPTURE", "RE_ANNOTATION", "RE_ORIENTATION"]), None)
        if latest_capture and latest_capture not in high_signal: high_signal.append(latest_capture)
        return sorted(high_signal, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]

    def search_archived_evidence(self, query_context: Dict[str, Any], limit: int = 2) -> List[Dict[str, Any]]:
        if not self.multimodal_history: return []
        candidates = []
        q_layer = str(query_context.get("layer") or "").lower()
        q_issue = str(query_context.get("issue_type") or "").lower()
        q_comp = str(query_context.get("component") or "").lower()
        archived = [h for h in self.multimodal_history if h.get("relevance") != "CRITICAL"]
        for h in archived:
            hyp = h.get("hypothesis", {})
            score = 0.0
            reasons = []
            if q_layer and hyp.get("layer") and q_layer in hyp["layer"].lower(): score += 0.4; reasons.append("Capa coincidente")
            if q_comp and hyp.get("component") and q_comp in hyp["component"].lower(): score += 0.3; reasons.append("Componente relacionado")
            if q_issue and hyp.get("issue_type") and q_issue in hyp["issue_type"].lower(): score += 0.2; reasons.append("Tipo de fallo similar")
            comment = str(h.get("creator_comment") or "").lower()
            if any(kw in comment for kw in q_layer.split('/') + q_issue.split('_')): score += 0.1; reasons.append("Similitud semántica")
            if score > 0.3:
                metadata = h.get("retrieval_metadata", {})
                metadata.update({
                    "relevance_score": round(score, 2), "match_reason": ", ".join(reasons), "recovered_at": datetime.now().isoformat(),
                    "cognitive_impact": {
                        "reinforced_strategy": f"Refuerza diagnóstico en {hyp.get('layer', 'capa compartida')}",
                        "historical_insight": hyp.get("description", "Sin detalle técnico previo"),
                        "influence": "HIGH" if score > 0.6 else "MEDIUM",
                        "impact_on_roadmap": hyp.get("roadmap_hint", "Continuar con plan actual")
                    },
                    "validation_status": metadata.get("validation_status", "PENDING")
                })
                h["retrieval_metadata"] = metadata
                candidates.append(h)
        return sorted(candidates, key=lambda x: x["retrieval_metadata"]["relevance_score"], reverse=True)[:limit]

    def get_compounded_context(self, active_query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        active = self.get_active_multimodal_context()
        active_ids = {h.get("id") for h in active if h.get("id")}
        for h in self.multimodal_history:
            react = h.get("manual_reactivation", {})
            if react.get("active") and h.get("id") not in active_ids:
                h_copy = dict(h); h_copy["relevance"] = "MANUAL_REACTIVATION"
                h_copy["impact_summary"] = f"[MANUAL RE-FOCUS] Reactivada por Creador. Motivo: {react.get('reason', 'Intervención manual')}"
                active.append(h_copy); active_ids.add(h.get("id"))
        if not active_query: return active
        recovered = self.search_archived_evidence(active_query, limit=2)
        for r in recovered:
            if r.get("retrieval_metadata", {}).get("validation_status") == "REJECTED": continue
            if r.get("id") not in active_ids:
                r_copy = dict(r); r_copy["relevance"] = "RECOVERED"
                impact = r_copy.get("retrieval_metadata", {}).get("cognitive_impact", {})
                r_copy["impact_summary"] = f"[RECALL IMPACT] {impact.get('reinforced_strategy', 'Análisis histórico')}. Insight: {impact.get('historical_insight', 'Evidencia previa')}"
                active.append(r_copy); active_ids.add(r_copy.get("id"))
        return active

    def validate_archival_recall(self, snapshot_id: str, approved: bool, reason: str = None):
        for h in self.multimodal_history:
            if h.get("id") == snapshot_id:
                meta = h.get("retrieval_metadata") or {"validation_status": "PENDING"}
                h["retrieval_metadata"] = meta
                meta["validation_status"] = "VALIDATED" if approved else "REJECTED"
                meta["human_comment"] = reason; meta["validated_at"] = datetime.now().isoformat()
                return True
        return False

    def reactivate_archival_snapshot(self, snapshot_id: str, active: bool, reason: str = None):
        for h in self.multimodal_history:
            if h.get("id") == snapshot_id:
                h["manual_reactivation"] = {"active": active, "reason": reason, "reactivated_at": datetime.now().isoformat() if active else None}
                if active and h.get("retrieval_metadata"): h["retrieval_metadata"]["validation_status"] = "VALIDATED"
                return True
        return False

    def search_multimodal_archive(self, query: str = None, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        results = []; q = (query or "").lower(); filters = filters or {}
        for h in self.multimodal_history:
            score = 0; hyp = h.get("hypothesis", {}); comment = str(h.get("creator_comment") or "").lower()
            if q:
                if q in comment: score += 50
                if q in str(hyp.get("description", "")).lower(): score += 30
                if q in str(hyp.get("layer", "")).lower(): score += 20
                if q in str(hyp.get("component", "")).lower(): score += 20
            match_filter = True
            if filters.get("layer") and filters["layer"].lower() not in str(hyp.get("layer", "")).lower(): match_filter = False
            if filters.get("issue_type") and filters["issue_type"].lower() not in str(hyp.get("issue_type", "")).lower(): match_filter = False
            if filters.get("status") and h.get("relevance") != filters["status"]: match_filter = False
            if match_filter and (score > 0 or not q):
                h_res = dict(h); h_res["search_score"] = score; results.append(h_res)
        return sorted(results, key=lambda x: x["search_score" if q else "timestamp"], reverse=True)

    def analyze_cognitive_drift(self) -> Dict[str, Any]:
        excluded = self.parameters.get("excluded_nodes", [])
        m_history = [h for h in self.multimodal_history if h.get("id") not in excluded]
        if not m_history: return {"status": "ALIGNED", "drift_score": 0, "reason": "Misión en fase inicial."}
        
        original_hyp = next((h.get("hypothesis", {}) for h in m_history if h.get("hypothesis")), {})
        current_hyp = next((h.get("hypothesis", {}) for h in reversed(m_history) if h.get("hypothesis")), {})
        orig_layer = str(original_hyp.get("layer", "unknown")).lower()
        curr_layer = str(current_hyp.get("layer", "unknown")).lower()
        
        active_ctx = self.get_compounded_context(active_query=current_hyp)
        manual_refs = [h for h in active_ctx if h.get("relevance") == "MANUAL_REACTIVATION"]
        recovered_refs = [h for h in active_ctx if h.get("relevance") == "RECOVERED"]
        
        drift_score = 0; reasons = []
        if orig_layer != curr_layer and orig_layer != "unknown": drift_score += 40; reasons.append(f"Cambio de capa técnica: de '{orig_layer}' a '{curr_layer}'.")
        if len(manual_refs) > 1: drift_score += 20; reasons.append(f"Alta influencia de memoria manual ({len(manual_refs)} nodos reactivados).")
        elif len(recovered_refs) > 2: drift_score += 15; reasons.append("Multiples recuperaciones automáticas influyendo en el razonamiento actual.")
        
        goal_keywords = set(self.active_goal.lower().split())
        layer_keywords = set(curr_layer.replace("/", " ").split())
        if not goal_keywords.intersection(layer_keywords) and orig_layer != "unknown": drift_score += 10; reasons.append("Baja correlación textual entre el objetivo inicial y la capa actual.")
        
        drift_class = "ALIGNED"
        if drift_score >= 80: drift_class = "CRITICAL_DRIFT"
        elif drift_score >= 60: drift_class = "DRIFT_WARNING"
        elif drift_score >= 40: drift_class = "ATTENTION_REQUIRED"
        elif drift_score >= 20: drift_class = "MINOR_SHIFT"
        
        recommendation = "RE-ORIENTACIÓN REQUERIDA." if drift_class == "CRITICAL_DRIFT" else "Revisar focos históricos." if drift_class == "DRIFT_WARNING" else "Validar si el cambio de capa está justificado." if drift_class == "ATTENTION_REQUIRED" else "Continuar ejecución nominal."

        # --- DRIFT SYNC HARDENING (PHASE 80) ---
        if drift_score > 40:
             try:
                  from backend.core.ai_host.governance.drift_detector import drift_detector, DriftAlert, DriftType, DriftSeverity
                  msg = f"Deriva cognitiva en aumento: Score {drift_score:.0f}. El foco '{orig_layer}' está perdiendo alineación."
                  alert = DriftAlert(
                      type=DriftType.COGNITIVE,
                      severity=DriftSeverity.WARNING if drift_score < 70 else DriftSeverity.CRITICAL,
                      message=msg,
                      targets=[orig_layer],
                      suggestion="Reorientar foco táctico o sincronizar mapa cognitivo."
                  )
                  drift_detector.record_drift_event(alert)
             except: pass

        causal_chain = []; trigger_event = None
        for h in self.multimodal_history:
            h_layer = str(h.get("hypothesis", {}).get("layer", "")).lower()
            if h_layer and h_layer != orig_layer and orig_layer != "unknown":
                trigger_event = {"id": h.get("id"), "event": h.get("event"), "layer": h_layer, "role": "TRIGGER (First focus shift)", "timestamp": h.get("timestamp")}
                causal_chain.append(trigger_event); break
        
        for node in active_ctx:
            rel = node.get("relevance")
            if rel in ["MANUAL_REACTIVATION", "RECOVERED"]:
                causal_chain.append({"id": node.get("id"), "event": node.get("event"), "layer": node.get("hypothesis", {}).get("layer"), "role": f"CONTRIBUTOR ({rel})", "influence": "HIGH" if rel == "MANUAL_REACTIVATION" else "MEDIUM"})
        
        return {
            "status": drift_class, "drift_score": drift_score, "original_focus": orig_layer, "current_focus": curr_layer, "reasons": reasons, "causal_chain": causal_chain[:5], "trigger_event": trigger_event,
            "memory_pressure": {"manual": len(manual_refs), "recovered": len(recovered_refs)}, "recommendation": recommendation,
            "suggested_actions": self._generate_realignment_suggestions(drift_class, orig_layer, causal_chain, drift_score)
        }

    def _apply_swarm_consensus(self, action: Dict[str, Any], current_drift: float, drift_status: str) -> Dict[str, Any]:
        """
        CAPA 1 & 2 (PHASE 76): STRATEGIC SWARM CONSENSUS.
        Audits tactical suggestions through multiple internal evaluators.
        """
        f = action.get("forecast", {})
        conf = f.get("confidence", 0.5)
        
        # Policy: Only audit grey zone (0.5-0.85) OR theoretical suggestions
        is_grey = (0.5 <= conf <= 0.85)
        is_theoretical = (f.get("source") == "THEORETICAL")
        
        if not is_grey and not is_theoretical:
             return action
        
        print(f"DEBUG: [SWARM_CONSENSUS] -> Auditing: {action['type']} (Conf: {conf:.2f})")
        
        votes = []
        # 1. EVALUADOR: STRATEGIC LEARNING (ROI history)
        roi = f.get("delta", 0)
        if roi > 30: votes.append({"auditor": "ROI_FORCASTER", "vote": 1, "reason": f"Alto impacto proyectado (+{roi:.0f})."})
        elif roi < 10: votes.append({"auditor": "ROI_FORCASTER", "vote": -1, "reason": f"Impacto marginal ({roi:.0f})."})
        
        # 2. EVALUADOR: HEALING ENGINE (Penalties)
        cases = f.get("cases", 0)
        if cases > 10: votes.append({"auditor": "EXPERIENCE_ENGINE", "vote": 1, "reason": "Sólida base histórica (>10 casos)."})
        elif cases == 1: votes.append({"auditor": "EXPERIENCE_ENGINE", "vote": 0, "reason": "Evidencia escasa (1 caso)."})

        # 3. EVALUADOR: DRIFT ANALYZER (Status check)
        if drift_status in ["CRITICAL_DRIFT", "DRIFT_WARNING"]: votes.append({"auditor": "DRIFT_SENTRY", "vote": 1, "reason": f"Necesidad de realineación en {drift_status}."})
        elif drift_status == "MINOR_SHIFT": votes.append({"auditor": "DRIFT_SENTRY", "vote": -1, "reason": "Cambio no justifica exclusión aún."})

        # Consensus Resolution
        positive = len([v for v in votes if v["vote"] > 0])
        negative = len([v for v in votes if v["vote"] < 0])
        total = len(votes)
        
        # Status calculation
        status = "AGNOSTIC"
        if total == 0: status = "NO_DATA"
        elif positive == total: status = "STRONG_CONSENSUS"
        elif positive > negative: status = "PARTIAL_SUPPORT"
        elif negative > positive: status = "DIVIDED_CONFLICT"
        else: status = "NEUTRAL"
        
        # Adjust confidence
        adjustment = (positive - negative) * 0.05
        new_conf = max(0.1, min(1.0, conf + adjustment))
        
        action["consensus"] = {
            "status": status,
            "votes": votes,
            "score": positive - negative,
            "conf_before": conf,
            "conf_after": new_conf,
            "timestamp": datetime.now().isoformat()
        }
        action["forecast"]["confidence"] = new_conf
        return action

    def _generate_realignment_suggestions(self, status: str, orig_layer: str, trace: List[Dict[str, Any]], drift_score: float) -> List[Dict[str, Any]]:
        actions = []
        if status == "ALIGNED": return []
        if orig_layer != "unknown": actions.append({"type": "RESTORE_FOCUS", "label": f"Restaurar foco en: {orig_layer}", "description": "Reiniciar el grafo de objetivos técnicos.", "complexity": "LOW"})
        for item in trace:
            node_id = item.get("id") or "sys_unknown"
            if "CONTRIBUTOR" in item.get("role", ""): 
                 actions.append({
                     "type": "EXCLUDE_NODE", 
                     "node_id": node_id, 
                     "label": f"Excluir ruido: {item.get('event')} ({node_id[:6]})", 
                     "description": "Remover esta pieza de memoria.", 
                     "complexity": "QUICK"
                 })
        if status in ["DRIFT_WARNING", "CRITICAL_DRIFT"]: actions.append({"type": "FORCE_REORIENTATION", "label": "Lanzar Re-orientación Visual Manual", "description": "Forzar nueva captura.", "complexity": "HUMAN_REQUIRED"})
        history = []
        try:
             from backend.core.ai_host.memory.mission_manager import mission_manager
             history = mission_manager.learning_engine.get_contextual_intelligence(f"{orig_layer}:{status}")
        except Exception as e: logger.error(f"[MISSION_STATE] Suggestion enrichment failed: {e}")
        for action in actions:
             action["forecast"] = {"current_drift": drift_score, "predicted_drift": drift_score, "delta": 0, "confidence": 0.5, "source": "THEORETICAL"}
             match = next((h for h in history if h["action"] == action["type"]), None)
             if match:
                  avg_roi = float(match["avg_roi"] or 0); predicted = max(0, drift_score - avg_roi); delta = drift_score - predicted
                  action["forecast"] = {"current_drift": drift_score, "predicted_drift": predicted, "delta": delta, "confidence": float(match["confidence"]), "source": "HISTORICAL", "cases": match["cases"]}
                  action["label"] = f"{action['label']} (PROYECCIÓN: -{delta:.0f} DRIFT | Conf: {match['confidence']:.2f})"
             
             # CAPA 4 (PHASE 76): Multimodal Consensus Audit
             self._apply_swarm_consensus(action, drift_score, status)
             
        return actions[:3]

    def _handle_reversal_feedback(self, action: Dict[str, Any]):
        """
        CAPA 3 (PHASE 75): HUMAN REVERSAL INTERPRETATION.
        Detects if a manual action contradicts a recent auto-rescue.
        """
        if not self.multimodal_history: return
        
        # Look for recent auto-rescues (last 3 events)
        recent_auto = [h for h in self.multimodal_history[-3:] if h.get("event") == "MISSION_AUTO_RESCUE"]
        if not recent_auto: return
        
        last_auto = recent_auto[-1]
        is_reversal = False
        reason = "DESAUTORIZACIÓN MANUAL"
        
        # Logic: If auto was EXCLUDE_NODE and human is doing something with that same node
        if last_auto.get("action_type") == "EXCLUDE_NODE":
             if action["type"] in ["RESTORE_FOCUS", "FORCE_REORIENTATION"]:
                  is_reversal = True
                  reason = f"REVERSIÓN: El creador forzó realineación tras exclusión automática."

        if is_reversal:
             try:
                  from backend.core.ai_host.memory.mission_manager import mission_manager
                  ckey = last_auto.get("audit", {}).get("context_key")
                  if not ckey:
                       drift = self.analyze_cognitive_drift()
                       ckey = f"{drift.get('original_focus')}:{drift.get('status')}"
                  
                  mission_manager.learning_engine.record_rescue_failure(ckey, last_auto["action_type"])
                  
                  self.multimodal_history.append({
                      "timestamp": datetime.now().isoformat(),
                      "event": "COGNITIVE_HEALING",
                      "reason": reason,
                      "audit": {
                          "original_action": last_auto["action_type"],
                          "feedback": "NEGATIVE",
                          "source": "HUMAN_OVERRIDE"
                      }
                  })
             except Exception as e:
                  logger.error(f"[MISSION_STATE] Healing update failed: {e}")

    def execute_realignment_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        a_type = action.get("type"); before_state = self.analyze_cognitive_drift()
        self._handle_reversal_feedback(action)
        
        result = {"success": False, "message": "Acción desconocida", "type": a_type}
        if a_type == "RESTORE_FOCUS":
             orig_focus = before_state.get("original_focus", "unknown")
             if orig_focus != "unknown": self.active_goal = f"[RESTORED] {self.active_goal}"; result = {"success": True, "message": f"Foco restaurado a '{orig_focus}'.", "type": a_type}
        elif a_type == "EXCLUDE_NODE":
             ex_nodes = self.parameters.get("excluded_nodes", []); ex_nodes.append(action.get("node_id")); self.parameters["excluded_nodes"] = list(set(ex_nodes))
             result = {"success": True, "message": "Nodo excluido.", "type": a_type}
        elif a_type == "FORCE_REORIENTATION": result = {"success": True, "message": "Re-orientación forzada.", "type": a_type}
        
        self.parameters["last_alerted_drift"] = "ALIGNED"; after_state = self.analyze_cognitive_drift()
        drift_delta = before_state["drift_score"] - after_state["drift_score"]
        impact = "HIGH_IMPACT_RECOVEY" if drift_delta > 10 else "MARGINAL_RECOVERY" if drift_delta > 0 else "STAGNANT" if drift_delta == 0 else "DETERIORATED"
        perf_audit = {"timestamp": datetime.now().isoformat(), "action": a_type, "drift_before": before_state["drift_score"], "drift_after": after_state["drift_score"], "delta": drift_delta, "impact": impact, "class_before": before_state["status"], "class_after": after_state["status"]}
        self.multimodal_history.append({"id": str(uuid.uuid4()), "event": f"REALIGNMENT_ROI: {a_type}", "timestamp": datetime.now().isoformat(), "performance": perf_audit, "governance": {"action_type": a_type, "authorized_by": "Creator"}})
        
        if result["success"]:
             try:
                  from backend.core.ai_host.memory.mission_manager import mission_manager
                  mission_manager.learning_engine.record_rescue_success(context_key=f"{before_state.get('original_focus','any')}:{before_state.get('status','any')}", action_type=a_type, roi=drift_delta)
             except Exception as e: logger.error(f"[MISSION_STATE] Learning record failed: {e}")
        result["performance_audit"] = perf_audit
        return result

    def generate_strategic_post_mortem(self) -> StrategicPostMortem:
        drift_report = self.analyze_cognitive_drift()
        dom_pattern = f"{drift_report['original_focus']} -> {drift_report['current_focus']}"
        return StrategicPostMortem(summary="Misión finalizada. Ver resumen de auditoría.", dominant_pattern=dom_pattern, best_action="ANALYSIS", avg_roi=0, reusable_lesson="Foco consolidado.", confidence=1.0)

    def generate_handoff(self, next_steps: List[str] = None) -> MissionHandoff:
        drift = self.analyze_cognitive_drift()
        return MissionHandoff(
            mission_id=self.mission_id, goal=self.active_goal, executive_summary=f"Misión finalizada con estado {drift['status']}.", technical_impact="Consolidado.",
            timeline_milestones=[f"Cierre: {datetime.now().isoformat()}"], governance_footprint={"score": (max(0, 100-drift["drift_score"])/100.0)},
            multimodal_evidence_refs=[], recovery_events=[], final_status=self.status,
            next_steps=next_steps or ["Auditoría final"], post_mortem=self.generate_strategic_post_mortem()
        )

    def generate_pre_mission_briefing(self) -> Dict[str, Any]:
        """
        CAPA 2 & 4 (PHASE 70): PRE-MISSION STRATEGIC BRIEFING.
        """
        m_history = self.multimodal_history
        if not m_history: return {"status": "NEW", "wisdom": []}
        initial_hyp = next((h.get("hypothesis", {}) for h in m_history if h.get("hypothesis")), {})
        layer = str(initial_hyp.get("layer", "unknown")).lower()
        if layer == "unknown": return {"status": "DOMAIN_UNKNOWN", "wisdom": []}
        
        lessons = []
        try:
             from backend.core.ai_host.memory.mission_manager import mission_manager
             wisdom = mission_manager.learning_engine.get_preventive_wisdom(layer)
             for w in wisdom:
                  lessons.append({"context": f"En {layer}", "warning": f"Deriva de {w['expected_impact']:.0f} detectada antes.", "recommendation": w['best_tactic'], "confidence": w["confidence"]})
        except: pass
        return {"status": "WISDOM_INJECTED" if lessons else "NO_HISTORY", "target_layer": layer, "lessons": lessons}

    def generate_cognitive_replay_trace(self) -> List[Dict[str, Any]]:
        """
        CAPA 1 & 2 (PHASE 71): COGNITIVE REPLAY ENGINE.
        """
        replay = []
        for i, h in enumerate(self.multimodal_history):
            replay.append({"step": i+1, "event": h.get("event"), "timestamp": h.get("timestamp")})
        return replay

    def generate_deep_recovery_plan(self) -> Dict[str, Any]:
        """
        CAPA 1, 2 & 3 (PHASE 80): COGNITIVE RECOVERY ENGINE.
        Synthesizes a strategic plan to resume an interrupted mission.
        """
        drift = self.analyze_cognitive_drift()
        last_focus = drift.get("original_focus", "global")
        scenarios = self.generate_mitigation_scenarios()
        
        # Recovery specific: context restore scenario
        if drift.get("drift_score", 0) < 20:
             scenarios.append({
                 "id": "scenario_safe_restore", "label": "RESTAURACIÓN DE CONTEXTO", "action": "RESTORE_EXECUTION_CONTEXT",
                 "projected_drift": 0, "projected_delta": drift.get("drift_score", 0), "risk_score": 5, "confidence": 0.98, "net_value": 95.0, "is_recommended": True,
                 "reasoning": "Foco estable. Continuar ejecución nominal.", "historical_experience": {"status": "SUPPORTED", "basis": "Patrón validado."}
             })

        best_scenario = next((s for s in scenarios if s.get("is_recommended")), None)
        policy_eval = self.evaluate_recovery_auto_policy(best_scenario)

        return {
            "mission_id": self.mission_id, 
            "recovered_at": datetime.now().isoformat(), 
            "focal_context": last_focus, 
            "drift_on_recovery": drift.get("drift_score", 0),
            "suggested_path": best_scenario, 
            "is_auto_eligible": policy_eval.get("allow_auto", False), 
            "policy_decision": policy_eval,
            "recovery_status": "STRATEGIC_READY" if best_scenario else "PASSIVE_RESTORE",
            "recovery_markdown": self._format_recovery_md(last_focus, best_scenario, {}, policy_eval)
        }

    def _format_recovery_md(self, focus: str, scenario: Dict[str, Any], wisdom: Dict[str, Any], policy: Dict[str, Any] = None) -> str:
        md = f"## 🔋 RECUPERACIÓN ESTRATÉGICA ACTIVA\nFoco: **{focus}**\n\n"
        if policy:
             icon = "🚀" if policy.get("allow_auto") else "🛡️"
             md += f"> {icon} **POLÍTICA:** {policy['reason']}\n\n"
        if scenario:
             md += f"### 🛠️ Ruta de Continuidad\n- **Acción:** {scenario['label']}\n- **Razonamiento:** {scenario['reasoning']}\n"
        return md

    def evaluate_recovery_auto_policy(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        CONSTITUTIONAL GUARD (PHASE 80): MISSION RECOVERY AUTO-EXECUTION POLICY.
        HARDENING: Enforces 'Freeze Sector' integrity during auto-recovery.
        """
        if not scenario: return {"allow_auto": False, "reason": "No scenario."}
        
        # 0. FREEZE INTEGRITY CHECK (MISSION GOVERNANCE HARDENING)
        params = self.parameters
        drift = self.analyze_cognitive_drift()
        orig_layer = drift.get("original_focus", "unknown").lower()
        
        frozen = params.get("frozen_layers", []) + params.get("frozen_paths", [])
        forbidden = params.get("forbidden_layers", []) + params.get("forbidden_paths", [])
        
        if any(layer.lower() in orig_layer for layer in frozen + forbidden):
             return {
                 "allow_auto": False, "level": "CREATOR_REQUIRED",
                 "reason": f"BLOQUEO CONSTITUCIONAL: El foco '{orig_layer}' está bajo FREEZE/FORBIDDEN. Autonomía suspendida por integridad."
             }

        # 1. Action Whitelist
        whitelist = ["RESTORE_EXECUTION_CONTEXT", "SILENT_SWARM_AUDIT", "REFRESH_COGNITIVE_MAP", "AUTO_ACKNOWLEDGE_MINOR_DRIFT"]
        
        action = scenario.get("action")
        confidence = scenario.get("confidence", 0)
        risk = scenario.get("risk_score", 100)
        
        if action not in whitelist: return {"allow_auto": False, "reason": f"Acción '{action}' fuera de lista blanca."}
        if confidence < 0.90: return {"allow_auto": False, "reason": f"Baja confianza ({confidence*100:.0f}%)."}
        if risk > 20: return {"allow_auto": False, "reason": f"Riesgo colateral elevado ({risk}%)."}
        if drift.get("drift_score", 0) > 40: return {"allow_auto": False, "reason": "Deriva excesiva."}
        
        return {"allow_auto": True, "reason": "Ruta segura y reversible.", "level": "AUTO_SAFE"}

    def execute_recovery_auto_action(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        policy = plan.get("policy_decision", {})
        if not policy.get("allow_auto"): return {"success": False, "message": "Policy denied."}
        scenario = plan.get("suggested_path")
        if not scenario: return {"success": False, "message": "No scenario."}

        self.multimodal_history.append({
            "timestamp": datetime.now().isoformat(), "event": "RECOVERY_AUTO_CONTINUITY",
            "action": scenario["action"], "label": scenario["label"], "policy_reason": policy["reason"],
            "audit": {"confidence": scenario["confidence"], "risk": scenario.get("risk_score", 0), "status": "EXECUTED_SILENTLY"}
        })
        return {"success": True, "action_executed": scenario["label"], "message": "Auto-continuación completada."}

    def evaluate_auto_rescue_eligibility(self) -> Optional[Dict[str, Any]]:
        scenarios = self.generate_mitigation_scenarios()
        candidates = [s for s in scenarios if s.get("autonomy_audit", {}).get("allow_auto") and s.get("confidence", 0) >= 0.90]
        if not candidates: return None
        return sorted(candidates, key=lambda x: x.get("projected_delta", 0), reverse=True)[0]

    def trigger_automatic_rescue(self) -> Dict[str, Any]:
        eligible = self.evaluate_auto_rescue_eligibility()
        if not eligible: return {"success": False, "message": "No action eligible."}
        pre_drift = self.analyze_cognitive_drift()
        result = self.execute_realignment_action({"type": eligible["action"], "node_id": eligible.get("node_id"), "label": eligible["label"]})
        if result.get("success"):
            self.multimodal_history.append({
                "timestamp": datetime.now().isoformat(), "event": "MISSION_AUTO_RESCUE", "action_type": eligible["action"],
                "audit": {"confidence": eligible["confidence"], "delta": eligible["projected_delta"], "pre_drift": pre_drift.get("drift_score")}
            })
            try:
                from backend.core.ai_host.governance.drift_detector import drift_detector, DriftAlert, DriftType, DriftSeverity
                drift_detector.record_drift_event(DriftAlert(type=DriftType.RESCUE, severity=DriftSeverity.INFO, message=f"🚀 AUTO-RESCUE: {eligible['label']}", targets=[pre_drift.get("original_focus")]))
            except: pass
        return result

    # --- PHASE 80: AUDIT ENGINE ---

    def perform_autonomy_audit(self) -> Dict[str, Any]:
        inventory = {"surfaces": [{"name": "RecoveryPolicy", "status": "ACTIVE"}, {"name": "ConstitutionalDrift", "status": "ACTIVE"}]}
        issues = []
        if self.parameters.get("frozen_layers"):
             issues.append({"surface": "RecoveryPolicy", "recommendation": "POLÍTICA ENDURECIDA: Freeze bloquea auto-recovery."})
        
        matrix = {"auto_safe": ["RESTORE_CONTEXT"], "human_confirm": ["RESTORE_FOCUS"], "pin_required": ["CORE_MUTATION"]}
        health = 1.0 - (len(issues) * 0.1)
        report = {"status": "GREEN" if health > 0.9 else "YELLOW", "health_score": health, "inventory": inventory, "decision_matrix": matrix, "detected_issues": issues,
                  "audit_markdown": self._format_audit_md("GREEN" if health > 0.9 else "YELLOW", inventory, issues, matrix)}
        self.last_audit_report = report
        return report

    def get_live_drift_snapshot(self) -> Dict[str, Any]:
        """
        CAPA 1 (PHASE 81): LIVE DRIFT SNAPSHOT MODEL.
        Provides a real-time snapshot of the cognitive health of the mission.
        """
        drift = self.analyze_cognitive_drift()
        audit = self.perform_autonomy_audit()
        
        # Calculate trend (Simplified: compare with last score if available in parameters)
        last_score = self.parameters.get("last_drift_score", drift["drift_score"])
        trend = "STABLE"
        if drift["drift_score"] > last_score: trend = "UP"
        elif drift["drift_score"] < last_score: trend = "DOWN"
        self.parameters["last_drift_score"] = drift["drift_score"]

        # Consensus and Healing
        consensus = "STABLE"
        healing = "NOMINAL"
        suggested = "Analizar deriva"
        if drift.get("suggested_actions"):
             suggested = drift["suggested_actions"][0]["label"]
             consensus_data = drift["suggested_actions"][0].get("consensus", {})
             if isinstance(consensus_data, dict):
                  consensus = consensus_data.get("status", "STABLE")
        
        # Detect healing/recovery events in history
        last_recovery = next((h for h in reversed(self.multimodal_history) if h.get("event") == "AUTO_RECOVERY"), None)
        if last_recovery: healing = "HEALING_ACTIVE"

        return {
            "mission_id": self.mission_id,
            "goal": self.active_goal[:40] + "..." if len(self.active_goal) > 40 else self.active_goal,
            "drift_score": drift["drift_score"],
            "drift": drift["status"], # Match frontend expectation
            "drift_trend": trend,
            "governance_state": audit["status"],
            "last_auto_rescue": last_recovery.get("timestamp") if last_recovery else None,
            "recovery_status": healing,
            "healing_state": healing,
            "consensus_state": consensus,
            "current_focus": drift.get("current_focus", "unknown"), # Match frontend
            "urgency": "HIGH" if drift["status"] in ["CRITICAL_DRIFT", "DRIFT_WARNING"] else "NORMAL", # Match frontend
            "suggested_action": suggested, # Match frontend
            "urgency_rank": 100 if drift["status"] == "CRITICAL_DRIFT" else 50 if drift["status"] == "DRIFT_WARNING" else 10 if drift["status"] == "ATTENTION_REQUIRED" else 0
        }

    def _format_audit_md(self, status: str, inv: Dict[str, Any], issues: List[Dict[str, Any]], matrix: Dict[str, Any]) -> str:
        icon = "🟢" if status == "GREEN" else "🟡"
        md = f"## {icon} AUDITORÍA CONSTITUCIONAL: {status}\n"
        if issues:
             md += "### 🛡️ Hardening Activo\n"
             for i in issues: md += f"- **{i['recommendation']}**\n"
        md += "\n> Veredicto: Constitución endurecida."
        return md

    def consolidate_mission_knowledge(self):
        try:
             from backend.core.ai_host.memory.mission_manager import mission_manager
             engine = mission_manager.learning_engine
             for h in self.multimodal_history:
                  if h.get("event") == "REALIGNMENT_ROI" and h.get("performance", {}).get("roi", 0) > 40:
                       engine.record_strategic_lesson(self.mission_id, "TACTIC_SUCCESS", "global", f"Exitosa realineación.")
        except: pass

    def _enrich_scenario_with_history(self, action: str, layer: str, wisdom: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"lessons": [], "strategic_weight": 0, "status": "NEUTRAL", "basis": "Simulación táctica."}

    def _evaluate_collateral_risk(self, action: str, layer: str) -> Dict[str, Any]:
        score = 50 if "core" in (layer or "").lower() else 10
        return {"score": score, "level": "HIGH" if score > 40 else "LOW"}

    def generate_mitigation_scenarios(self) -> List[Dict[str, Any]]:
        drift = self.analyze_cognitive_drift(); score = drift.get("drift_score", 0); layer = drift.get("original_focus", "global")
        scenarios = [{
            "id": "scenario_baseline", "label": "MANTENER", "action": "NONE", "projected_drift": score, "projected_delta": 0, "confidence": 1.0, "net_value": 0, "is_recommended": False,
            "autonomy_audit": {"allow_auto": False}
        }]
        for i, a in enumerate(drift.get("suggested_actions", [])):
             audit = self.evaluate_mitigation_autonomy(a["type"], layer, a.get("forecast", {}).get("confidence", 0.5))
             scenarios.append({
                 "id": f"scenario_tac_{i}", "label": a["label"], "action": a["type"], "projected_drift": 0, "projected_delta": score, "risk_score": 10, "net_value": 50,
                 "confidence": 0.8, "is_recommended": True, "autonomy_audit": audit, "reasoning": a["description"]
             })
        return scenarios

    def evaluate_mitigation_autonomy(self, action: str, layer: str, conf: float) -> Dict[str, Any]:
        if "core" in (layer or "").lower(): return {"level": "PIN_REQUIRED", "is_blocked": True, "allow_auto": False}
        return {"level": "HUMAN_CONFIRM", "is_blocked": False, "allow_auto": False}
