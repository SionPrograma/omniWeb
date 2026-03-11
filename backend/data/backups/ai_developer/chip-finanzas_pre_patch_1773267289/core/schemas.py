from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Transaction(BaseModel):
    id: Optional[int] = None
    type: str
    amount: float
    desc: str
    date: Optional[str] = None

class TransactionResponse(BaseModel):
    status: str
    transaction: Transaction
