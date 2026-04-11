from typing import List, Optional
from datetime import datetime
from backend.core.database import db_manager
from .schemas import Transaction

class FinanzasRepository:
    """
    Handles SQLite persistence for chip-finanzas.
    Encapsulates raw SQL and basic CRUD operations.
    """
    def __init__(self):
        self._db_initialized = False

    def _ensure_db(self):
        """Ensures the database is initialized before any operation (Lazy Init)."""
        if not self._db_initialized:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("FINANZAS: Lazy-initializing repository database...")
            self.init_db()
            self._db_initialized = True

    def init_db(self):
        """Initializes the transactions table if it doesn't exist."""
        # This call is now safe as it's deferred until a real request hits.
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    desc TEXT NOT NULL,
                    date TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_all(self) -> List[Transaction]:
        self._ensure_db()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
            rows = cursor.fetchall()
            return [Transaction(**dict(row)) for row in rows]

    def add(self, tx: Transaction) -> Transaction:
        self._ensure_db()
        date_str = tx.date or datetime.now().isoformat()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (type, amount, desc, date) VALUES (?, ?, ?, ?)",
                (tx.type, tx.amount, tx.desc, date_str)
            )
            tx.id = cursor.lastrowid
            tx.date = date_str
            conn.commit()
            return tx

# Global instance
finanzas_repo = FinanzasRepository()
