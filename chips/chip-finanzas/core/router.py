from fastapi import APIRouter
from typing import List
from .schemas import Transaction, TransactionResponse
from .service import finanzas_service

# El prefix global de /api/v1/finanzas ya lo provee el module_registry en backend/main.py
router = APIRouter(tags=["finanzas"])

@router.get("/transactions", response_model=List[Transaction])
async def list_transactions():
    """
    Lista de movimientos desde el backend (persistencia SQLite).
    """
    return finanzas_service.list_movements()

@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(tx: Transaction):
    """
    Guarda un movimiento en la base de datos persistente.
    """
    new_tx = finanzas_service.record_movement(tx)
    return TransactionResponse(status="success", transaction=new_tx)
