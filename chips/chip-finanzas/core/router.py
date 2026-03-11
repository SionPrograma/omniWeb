from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# El prefix global de /api/v1/finanzas ya lo provee el module_registry en backend/main.py
router = APIRouter(tags=["finanzas"])

class Transaction(BaseModel):
    id: Optional[int] = None
    type: str
    amount: float
    desc: str
    date: Optional[str] = None

class TransactionResponse(BaseModel):
    status: str
    transaction: Transaction

# Base de datos en memoria transicional (Fallback backend)
MOCK_DB: List[Transaction] = [
    Transaction(id=1, type="income", amount=2500.00, desc="Salario (Desde Servidor)", date=datetime.now().isoformat()),
    Transaction(id=2, type="expense", amount=45.00, desc="Supermercado (Desde Servidor)", date=datetime.now().isoformat())
]

@router.get("/transactions", response_model=List[Transaction])
async def list_transactions():
    """
    Lista de movimientos desde el backend.
    """
    return MOCK_DB

@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(tx: Transaction):
    """
    Guarda un movimiento en la memoria efímera del servidor.
    """
    if not tx.id:
        tx.id = int(datetime.now().timestamp() * 1000)
    if not tx.date:
        tx.date = datetime.now().isoformat()
        
    MOCK_DB.insert(0, tx)
    return TransactionResponse(status="success", transaction=tx)
