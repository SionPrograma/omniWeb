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
        self.init_db()

    def init_db(self):
        """Initializes the transactions table if it doesn't exist."""
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
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
            rows = cursor.fetchall()
            return [Transaction(**dict(row)) for row in rows]

    def add(self, tx: Transaction) -> Transaction:
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
