
import logging
from typing import List, Dict, Any, Optional
from ..memory.mission_manager import mission_manager, MissionState

logger = logging.getLogger(__name__)

class MultimodalReportGenerator:
    """
    CAPA 1: Multimodal Mission Reporting.
    Consolidates the fragmented multimodal history into a coherent timeline.
    """
    
    def generate_report(self, mission_id: str) -> Optional[Dict[str, Any]]:
        mission = mission_manager.get_active_mission()
        if not mission or mission.mission_id != mission_id:
            # Try to load from DB directly if not the active one
            mission = self._load_mission(mission_id)
            
        if not mission:
            return None
            
        history = mission.multimodal_history
        visual_ctx = mission.visual_context
        
        report = {
            "mission_id": mission.mission_id,
            "goal": mission.active_goal,
            "status": mission.status.value,
            "timeline": []
        }
        
        # 1. Capture Nodes from History
        for entry in history:
            event = entry.get("event")
            node = {
                "timestamp": entry.get("timestamp"),
                "event": event,
                "description": entry.get("creator_comment", ""),
                "hypothesis": entry.get("hypothesis"),
                "annotations": entry.get("annotations"),
                "visual_diff": entry.get("visual_diff"),
                "relevance": entry.get("relevance", "SUPPORT"), # PHASE 55: Context Pruning
                "retrieval_metadata": entry.get("retrieval_metadata"), # PHASE 56: Semantic Retrieval
                "impact_summary": entry.get("impact_summary") # PHASE 57: Explainability Trace
            }
            
            if event == "INITIAL_CAPTURE":
                node["title"] = "Evidencia Inicial Recibida"
                node["type"] = "input"
            elif event == "RE_ORIENTATION":
                node["title"] = "Re-orientación Visual (Feedback Creador)"
                node["type"] = "correction"
                # Enrich with diff summary
                diff = entry.get("visual_diff", {})
                if diff:
                    node["diff_summary"] = f"+{diff.get('added_count', 0)} / -{diff.get('removed_count', 0)} regiones"
            
            report["timeline"].append(node)
            
        # 2. Add Technical Refinement Node (Latest Pulse)
        if visual_ctx and visual_ctx.get("hypothesis"):
            hyp = visual_ctx["hypothesis"]
            report["technical_refinement"] = {
                "layer": hyp.get("layer"),
                "component": hyp.get("component"),
                "route": hyp.get("route"),
                "confidence": hyp.get("confidence"),
                "issue_type": hyp.get("issue_type"),
                "roadmap_hint": hyp.get("roadmap_hint")
            }
            
        # 3. Add Rescue/Action Node
        # We look into mission nodes for Rescue or Completed Construction
        tree = mission.context_snap.get("tree")
        if tree:
            rescue_nodes = self._find_nodes_by_label(tree["root"], "RESCUE")
            if rescue_nodes:
                report["rescue_impact"] = [
                    {
                        "step": n["label"],
                        "summary": n.get("evidence"),
                        "trace": n.get("deep_evidence", {}).get("cognitive_trace")
                    } for n in rescue_nodes
                ]
                
        # 4. Governance Status
        report["governance"] = {
            "health": mission.context_snap.get("governance_health"),
            "approval_required": mission.parameters.get("audit_only") is False,
            "decisions": [
                entry.get("gate_decision") for entry in mission.multimodal_history if entry.get("gate_decision")
            ]
        }
        
        return report

    def _load_mission(self, mission_id: str) -> Optional[MissionState]:
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT * FROM system_missions WHERE mission_id = ?", (mission_id,)).fetchone()
                if row:
                    return mission_manager._row_to_mission(row)
        return None

    def _find_nodes_by_label(self, node: Dict[str, Any], keyword: str) -> List[Dict[str, Any]]:
        found = []
        if keyword in node.get("label", "").upper() or keyword in str(node.get("id")).upper():
            found.append(node)
        for child in node.get("children", []):
            found.extend(self._find_nodes_by_label(child, keyword))
        return found

multimodal_report_generator = MultimodalReportGenerator()
