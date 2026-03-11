from typing import List, Optional
from chips.chip_reparto.core.repository import reparto_repo
from chips.chip_reparto.core.schemas import Stop

class RepartoService:
    """
    Business logic layer for chip-reparto.
    """
    def get_all_stops(self) -> List[Stop]:
        return reparto_repo.get_all()

    def update_delivery_status(self, stop_id: int, status: str) -> Optional[Stop]:
        # Lógica de negocio (ej: notificar llegada, actualizar GPS)
        return reparto_repo.update_status(stop_id, status)

# Global instance
reparto_service = RepartoService()
