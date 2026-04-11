import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

class SQLiteJobStore:
    """
    Durable Persistence Engine for chip-lingua.
    Stores job truth and progress history in a local SQLite ledger.
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table: lingua_jobs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lingua_jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT,
                    stage TEXT,
                    stage_completed TEXT,
                    percent REAL,
                    message TEXT,
                    result_url TEXT,
                    error TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Table: lingua_progress_history (Durable stage audit)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lingua_progress_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    stage TEXT,
                    percent REAL,
                    status TEXT,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (job_id) REFERENCES lingua_jobs(job_id)
                )
            """)

            # Table: lingua_purge_audit (V1.8 Governance Tracer)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lingua_purge_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    original_status TEXT,
                    reason TEXT,
                    purged_at TEXT,
                    media_cleared BOOLEAN
                )
            """)
            
            # Index for faster history retrieval
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON lingua_progress_history(job_id)")
            conn.commit()

    def delete_job(self, job_id: str):
        """Permanent deletion of job and history from operational tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lingua_progress_history WHERE job_id = ?", (job_id,))
            cursor.execute("DELETE FROM lingua_jobs WHERE job_id = ?", (job_id,))
            conn.commit()

    def log_purge(self, job_id: str, status: str, reason: str, media_cleared: bool = True):
        """Records a governance purge event."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lingua_purge_audit (job_id, original_status, reason, purged_at, media_cleared)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, status, reason, datetime.now().isoformat(), 1 if media_cleared else 0))
            conn.commit()

    def save_job(self, job_data: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO lingua_jobs 
                (job_id, status, stage, stage_completed, percent, message, result_url, error, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_data["job_id"],
                job_data["status"],
                job_data["stage"],
                job_data.get("stage_completed"),
                job_data["percent"],
                job_data["message"],
                job_data.get("result_url"),
                job_data.get("error"),
                job_data.get("created_at"),
                job_data["updated_at"]
            ))
            conn.commit()

    def add_progress_event(self, job_id: str, event: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lingua_progress_history (job_id, stage, percent, status, message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                event["stage"],
                event["percent"],
                event["status"],
                event["message"],
                event["timestamp"]
            ))
            conn.commit()

    def get_job(self, job_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM lingua_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row: return None
            
            job = dict(row)
            
            # Load History
            cursor.execute("SELECT * FROM lingua_progress_history WHERE job_id = ? ORDER BY id ASC", (job_id,))
            history = [dict(r) for r in cursor.fetchall()]
            job["progress_history"] = history
            
            return job

    def list_recent_jobs(self, limit=10) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lingua_jobs ORDER BY updated_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def load_all_jobs(self) -> dict:
        """Helper to restore in-memory state on startup."""
        all_jobs = {}
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT job_id FROM lingua_jobs")
            ids = [r[0] for r in cursor.fetchall()]
            
            for jid in ids:
                all_jobs[jid] = self.get_job(jid)
        return all_jobs

    def list_purge_audit(self, limit=50) -> list:
        """Retrieves history of purging decisions for governance visibility."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lingua_purge_audit ORDER BY purged_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def is_job_purged(self, job_id: str) -> bool:
        """Checks if a job exists in the purge audit log."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM lingua_purge_audit WHERE job_id = ?", (job_id,))
            return cursor.fetchone() is not None
