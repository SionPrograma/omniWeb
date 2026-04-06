import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from datetime import datetime

logger = logging.getLogger(__name__)

class RoadsideAssistantEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE TACTICAL ROADSIDE ASSISTANT.
    Live monitoring and contextual assistance during Roadmap execution.
    """
    
    def __init__(self):
        self.severity_map = {
            "ORDER_DEVIATION": "WARNING",
            "PRECONDITION_BROKEN": "CRITICAL",
            "NEW_PRESSURE_SPIKE": "WARNING",
            "BLOCKER_DETECTED": "CRITICAL",
            "PACKAGE_STALE": "INFO",
            "REPLAN_RECOMMENDED": "INFO"
        }

    def detect_events(self) -> List[Dict[str, Any]]:
        """
        Monitors the state and triggers tactical roadside assistance.
        """
        new_events = []
        
        # 1. Devio del Orden (The most common tactical deviation)
        deviation = self._check_order_deviation()
        if deviation: new_events.append(deviation)
        
        # 2. Precondiciones Rotas
        broken = self._check_preconditions()
        new_events.extend(broken)
        
        # 3. Presión espontánea (Heuristic: High risk on related domains)
        spikes = self._check_pressure_spikes()
        new_events.extend(spikes)

        self._persist_events(new_events)
        return new_events

    def _check_order_deviation(self) -> Optional[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            # Active missions
            active = conn.execute("SELECT mission_id, source_draft_id FROM system_missions WHERE status = 'active' LIMIT 1").fetchone()
            if not active: return None
            
            # Top of roadmap
            roadmap = conn.execute("SELECT * FROM governance_roadmap_optimizations ORDER BY suggested_rank ASC LIMIT 1").fetchone()
            if not roadmap: return None
            
            # Check if active is indeed the top suggested one
            # The roadmap.source_id is the package_id. We need to find if active mission came from that package.
            package = conn.execute("SELECT package_id FROM governance_action_packages WHERE realized_mission_id = ?", (active["mission_id"],)).fetchone()
            
            if not package or package["package_id"] != roadmap["source_id"]:
                return {
                    "event_id": f"ROADSIDE-{uuid.uuid4().hex[:8].upper()}",
                    "active_package_id": (package["package_id"] if package else "unknown"),
                    "source_roadmap_item_id": roadmap["item_id"],
                    "event_type": "ORDER_DEVIATION",
                    "severity_band": "WARNING",
                    "rationale": f"Ejecución fuera de secuencia. Se inició {active['mission_id']} pero el roadmap sugiere {roadmap['source_id']} como prioridad #1.",
                    "suggested_action": "Pausar o Re-priorizar Sequence #1",
                    "confidence": 0.95
                }
        return None

    def _check_preconditions(self) -> List[Dict[str, Any]]:
        # This is a stub for current phase: assuming some items are blocked.
        return []

    def _check_pressure_spikes(self) -> List[Dict[str, Any]]:
        # Stub for live pressure monitoring
        return []

    def _persist_events(self, events: List[Dict[str, Any]]):
        if not events: return
        with db_manager.get_connection() as conn:
            for e in events:
                # Basic Cooldown: Don't repeat same event type for same item in short time
                exists = conn.execute("""
                    SELECT event_id FROM governance_roadside_events 
                    WHERE event_type = ? AND (active_package_id = ? OR source_roadmap_item_id = ?) 
                    AND is_dismissed = 0 AND created_at > datetime('now','-5 minutes')
                """, (e["event_type"], e["active_package_id"], e["source_roadmap_item_id"])).fetchone()
                
                if exists: continue

                conn.execute("""
                    INSERT INTO governance_roadside_events (
                        event_id, active_package_id, source_roadmap_item_id, event_type, 
                        severity_band, rationale, suggested_action, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    e["event_id"], e["active_package_id"], e["source_roadmap_item_id"],
                    e["event_type"], e["severity_band"], e["rationale"], 
                    e["suggested_action"], e["confidence"]
                ))
            conn.commit()

    def list_active_events(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_roadside_events WHERE is_dismissed = 0 ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def process_event_action(self, event_id: str, decision: str) -> bool:
        """decision: IGNORED, ACCEPTED, RECALCULATED"""
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE governance_roadside_events 
                SET creator_decision = ?, is_dismissed = 1, updated_at = CURRENT_TIMESTAMP 
                WHERE event_id = ?
            """, (decision, event_id))
            conn.commit()
            return True

roadside_assistant = RoadsideAssistantEngine()
