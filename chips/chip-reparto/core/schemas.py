from pydantic import BaseModel
from typing import List, Dict, Any

class Stop(BaseModel):
    id: int
    name: str
    address: str
    orderId: str
    status: str

class StopStatusUpdate(BaseModel):
    status: str
