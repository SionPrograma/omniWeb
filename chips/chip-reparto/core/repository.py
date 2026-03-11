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
                    status TEXT NOT NULL,
                    lat REAL,
                    lng REAL
                )
            """)
            
            # Lazy migration: Add lat/lng columns if they don't exist (if table was created without them)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(stops)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'lat' not in columns:
                conn.execute("ALTER TABLE stops ADD COLUMN lat REAL")
            if 'lng' not in columns:
                conn.execute("ALTER TABLE stops ADD COLUMN lng REAL")

            # Seed data check
            cursor.execute("SELECT COUNT(*) FROM stops")
            if cursor.fetchone()[0] == 0:
                # Seed data with some initial coordinates for demo (Málaga)
                seed_data = [
                    (1, "Empresa Transportes A", "Calle Alameda Principal, Malaga, Spain", "RPT-001", "PENDIENTE", 36.7196, -4.4225),
                    (2, "Almacen Norte", "Calle Victoria, Malaga, Spain", "RPT-002", "PENDIENTE", 36.7242, -4.4162),
                    (3, "Cliente VIP 1", "Calle Larios, Malaga, Spain", "RPT-003", "PENDIENTE", 36.7188, -4.4217),
                    (4, "Despacho B", "Av. de Andalucia, Malaga, Spain", "RPT-004", "PENDIENTE", 36.7161, -4.4332)
                ]
                conn.executemany(
                    "INSERT INTO stops (id, name, address, orderId, status, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?)",
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

    def update_coordinates(self, stop_id: int, lat: float, lng: float):
        """Persiste las coordenadas obtenidas por geocodificación."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE stops SET lat = ?, lng = ? WHERE id = ?", (lat, lng, stop_id))
            conn.commit()

# Global instance
reparto_repo = RepartoRepository()
