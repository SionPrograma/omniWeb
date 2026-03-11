from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Stop(BaseModel):
    id: int
    name: str
    address: str
    orderId: str
    status: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class StopStatusUpdate(BaseModel):
    status: str
