import json
import sqlite3
from datetime import datetime, timedelta
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def seed_predictive_scenario():
    print("Seeding Predictive Drift Scenario...")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 1. Antipattern in CORE_ENGINE
            conn.execute("""
            INSERT OR REPLACE INTO governance_learning_items 
            (learning_item_id, learning_type, target_domain, lesson_summary, recommended_behavior, confidence, supporting_evidence, is_antipattern, occurrence_count, freshness, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("LI-VAL-1", "TACTIC_INEFFECTIVE_IN_CONTEXT", "CORE_ENGINE", "La táctica 'ACCEPT_RISK' resulta insuficiente en CORE_ENGINE.", "Revisar arquitectura antes de mas overrides.", 0.9, "{}", 1, 2, datetime.now().isoformat(), datetime.now().isoformat()))
            
            # 2. Recent trace that triggers the antipattern
            conn.execute("""
            INSERT OR REPLACE INTO governance_action_traces (trace_id, target_id, target_type, target_domain, creator_action, initial_severity, initial_fused_status, applied_at, outcome_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("TR-VAL-1", "MISSION-001", "MISSION", "CORE_ENGINE", "ACCEPT_RISK", "HIGH", "DRIFT", (datetime.now() - timedelta(hours=2)).isoformat(), "PENDING_OUTCOME"))
            
            # 3. Debt (Risk Override) on SECURITY (High risk = high friction)
            conn.execute("""
            INSERT OR REPLACE INTO governance_risk_overrides (override_id, target_id, override_type, risk_level, affected_domain, rationale, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("OR-VAL-1", "MISSION-SEC", "DEBT", "CRITICAL", "SECURITY", "Validación predictiva.", 1, datetime.now().isoformat()))
            
            conn.commit()
    print("Scenario seeded. Running Predictive Scan...")
    
    from backend.core.ai_host.observability.governance_predictive_engine import predictive_engine
    advisories = predictive_engine.scan_drift_signals()
    
    print(f"Drift Scan completed. Detected {len(advisories)} predictive signals.")
    for a in advisories:
        print(f" - [{a.predictive_state}] {a.target_domain}: {a.risk_projection}")
        print(f"   Confidence: {a.confidence} | Reason: {a.rationale}")

if __name__ == "__main__":
    seed_predictive_scenario()
