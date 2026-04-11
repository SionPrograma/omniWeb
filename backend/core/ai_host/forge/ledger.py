import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import Optional
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class ComparisonLedger:
    """
    Forge Comparison Ledger (Block 77).
    A persistent store for evidence-based evaluation of external tools.
    """
    def __init__(self):
        self.init_schema()

    def init_schema(self):
        """Ensures the comparison ledger and configuration tables exist."""
        with db_manager.get_connection(internal=True) as conn:
            # 1. Telemetry Ledger (Block 77/78)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_comparison_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_id TEXT NOT NULL,
                    capability_class TEXT NOT NULL,
                    task_context TEXT,
                    outcome_status TEXT NOT NULL, 
                    quality_score REAL DEFAULT 0.0,
                    latency_ms INTEGER DEFAULT 0,
                    cost_units REAL DEFAULT 0.0,
                    privacy_band TEXT,
                    controllability_band TEXT DEFAULT 'UNKNOWN',
                    notes TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. Active Overrides (Block 81)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_forge_overrides (
                    capability TEXT PRIMARY KEY,
                    active_provider_id TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    applied_by TEXT,
                    request_id INTEGER
                )
            """)
            
            # 3. Swap Requests (Block 81)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_swap_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capability TEXT NOT NULL,
                    from_provider TEXT NOT NULL,
                    to_provider TEXT NOT NULL,
                    context TEXT,
                    rationale TEXT,
                    strength TEXT,
                    tradeoff TEXT,
                    status TEXT DEFAULT 'PENDING',
                    rollback_state TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at DATETIME,
                    applied_at DATETIME
                )
            """)

            # 4. Context Affinity Memory (V2.0)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_forge_affinity_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chip_id TEXT DEFAULT 'lingua',
                    capability TEXT NOT NULL,
                    context_tag TEXT NOT NULL,
                    provider_id TEXT NOT NULL,
                    affinity_score REAL DEFAULT 0.0, -- -1.0 to 1.0
                    sample_count INTEGER DEFAULT 0,
                    outcome_trend TEXT DEFAULT 'STABLE', -- IMPROVING, DEGRADING, STABLE, MIXED
                    evidence_summary TEXT, -- JSON stats
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chip_id, capability, context_tag, provider_id)
                )
            """)

            # 5. Cross-Domain Sync Advisories (V2.1)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_forge_cross_sync_advisories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_chip TEXT NOT NULL,
                    target_chip TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    context_tag TEXT NOT NULL,
                    suggested_provider_id TEXT NOT NULL,
                    strength REAL DEFAULT 0.0,
                    rationale TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_chip, target_chip, capability, context_tag)
                )
            """)
            conn.commit()
        logger.info("Forge Comparison Ledger & Cross-Domain Sync schema initialized.")

    async def log_telemetry(self, telemetry: dict):
        """
        Records a telemetry payload into the ledger (non-blocking thread bridge).
        """
        import asyncio
        
        def _insert():
            with db_manager.get_connection(internal=True) as conn:
                conn.execute("""
                    INSERT INTO intelligence_comparison_ledger (
                        provider_id, capability_class, task_context, 
                        outcome_status, quality_score, latency_ms, 
                        cost_units, privacy_band, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    telemetry.get("provider_id"),
                    telemetry.get("capability_class"),
                    telemetry.get("task_context"),
                    telemetry.get("outcome_status"),
                    telemetry.get("quality_score", 0.0),
                    telemetry.get("latency_ms", 0),
                    telemetry.get("cost_units", 0.0),
                    telemetry.get("privacy_band"),
                    telemetry.get("notes")
                ))
                conn.commit()
        
        try:
            await asyncio.to_thread(_insert)
        except Exception as e:
            logger.error(f"Failed to log forge telemetry: {e}")

    async def list_history(self, provider_id: str = None, limit: int = 100):
        """Retrieves history for analysis or display."""
        def _fetch():
            with db_manager.get_connection(internal=True) as conn:
                query = "SELECT * FROM intelligence_comparison_ledger"
                params = []
                if provider_id:
                    query += " WHERE provider_id = ?"
                    params.append(provider_id)
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]
        
        return await asyncio.to_thread(_fetch)

    # BLOCK 81 METHODS
    async def create_swap_request(self, request_data: dict) -> int:
        def _insert():
            with db_manager.get_connection(internal=True) as conn:
                cursor = conn.execute("""
                    INSERT INTO intelligence_swap_requests (
                        capability, from_provider, to_provider, context,
                        rationale, strength, tradeoff
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_data['capability'],
                    request_data['from_provider'],
                    request_data['to_provider'],
                    request_data.get('context'),
                    request_data.get('rationale'),
                    request_data.get('strength'),
                    request_data.get('tradeoff')
                ))
                conn.commit()
                return cursor.lastrowid
        return await asyncio.to_thread(_insert)

    async def list_requests(self, status: str = None) -> list:
        def _fetch():
            with db_manager.get_connection(internal=True) as conn:
                query = "SELECT * FROM intelligence_swap_requests"
                params = []
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                query += " ORDER BY created_at DESC"
                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]
        return await asyncio.to_thread(_fetch)

    async def get_active_provider(self, capability: str) -> Optional[str]:
        def _fetch():
            with db_manager.get_connection(internal=True) as conn:
                row = conn.execute(
                    "SELECT active_provider_id FROM intelligence_forge_overrides WHERE capability = ?", 
                    (capability,)
                ).fetchone()
                return row['active_provider_id'] if row else None
        return await asyncio.to_thread(_fetch)

    def get_active_provider_sync(self, capability: str) -> Optional[str]:
        """Synchronous resolution for legacy bridges or workers."""
        with db_manager.get_connection(internal=True) as conn:
            row = conn.execute(
                "SELECT active_provider_id FROM intelligence_forge_overrides WHERE capability = ?", 
                (capability,)
            ).fetchone()
            return row['active_provider_id'] if row and row['active_provider_id'] != "DEFAULT" else None

    async def apply_swap(self, request_id: int):
        def _apply():
            with db_manager.get_connection(internal=True) as conn:
                req = conn.execute("SELECT * FROM intelligence_swap_requests WHERE id = ?", (request_id,)).fetchone()
                if not req: return False
                
                # Snapshot current
                current = conn.execute("SELECT active_provider_id FROM intelligence_forge_overrides WHERE capability = ?", (req['capability'],)).fetchone()
                rollback = current['active_provider_id'] if current else "DEFAULT"
                
                # Apply
                conn.execute("""
                    INSERT OR REPLACE INTO intelligence_forge_overrides (capability, active_provider_id, request_id)
                    VALUES (?, ?, ?)
                """, (req['capability'], req['to_provider'], request_id))
                
                # Update Request
                conn.execute("""
                    UPDATE intelligence_swap_requests SET status = 'APPLIED', rollback_state = ?, applied_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (rollback, request_id))
                conn.commit()
                return True
        return await asyncio.to_thread(_apply)

# Global singleton
forge_ledger = ComparisonLedger()
