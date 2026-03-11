from typing import List
from chips.chip_finanzas.core.repository import finanzas_repo
from chips.chip_finanzas.core.schemas import Transaction

class FinanzasService:
    """
    Business logic layer for chip-finanzas.
    Coordinates between Router and Repository.
    """
    def list_movements(self) -> List[Transaction]:
        # Here we could add logic to filter by month, recurring expenses, etc.
        return finanzas_repo.get_all()

    def record_movement(self, tx: Transaction) -> Transaction:
        # Lógica de negocio (ej: validar topes de gastos, enviar alertas)
        return finanzas_repo.add(tx)

# Global instance
finanzas_service = FinanzasService()
