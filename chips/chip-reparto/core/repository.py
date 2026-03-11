from typing import List, Optional
from backend.core.database import db_manager
from .schemas import Stop

class RepartoRepository:
    """
    Handles SQLite persistence for chip-reparto.
    """
    def __init__(self):
        self.init_db()

    def init_db(self):
        """Initializes the stops table with seed data if empty."""
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stops (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    orderId TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            
            # Seed data check
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stops")
            if cursor.fetchone()[0] == 0:
                seed_data = [
                    (1, "Empresa de Transportes A", "Av. Principal 123", "RPT-001", "PENDIENTE"),
                    (2, "Almacen Norte", "Calle Industrial 45", "RPT-002", "PENDIENTE"),
                    (3, "Cliente VIP 1", "Boulevard Central 89", "RPT-003", "PENDIENTE"),
                    (4, "Despacho B", "Av. Costanera 101", "RPT-004", "PENDIENTE")
                ]
                conn.executemany(
                    "INSERT INTO stops (id, name, address, orderId, status) VALUES (?, ?, ?, ?, ?)",
                    seed_data
                )
            conn.commit()

    def get_all(self) -> List[Stop]:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM stops")
            rows = cursor.fetchall()
            return [Stop(**dict(row)) for row in rows]

    def update_status(self, stop_id: int, status: str) -> Optional[Stop]:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE stops SET status = ? WHERE id = ?", (status, stop_id))
            if cursor.rowcount == 0:
                return None
            conn.commit()
            
            cursor.execute("SELECT * FROM stops WHERE id = ?", (stop_id,))
            row = cursor.fetchone()
            return Stop(**dict(row))

# Global instance
reparto_repo = RepartoRepository()
