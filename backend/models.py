from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class EntityModel(BaseModel):
    id: str
    type: str
    position: list[float]
    name: Optional[str] = None
    birthdate: Optional[str] = None
    health: Optional[int] = None
    hunger: Optional[int] = None

class EntityUpdateModel(BaseModel):
    name: str
    birthdate: str

class PositionUpdateModel(BaseModel):
    position: list[float]

class TileModel(BaseModel):
    id: str
    gridX: int
    gridZ: int
    type: str
    crops: List[Dict[str, Any]] = []
    
class FarmerModel(EntityModel):
    inventoryJSON: Optional[str] = "{}"
    memoryJSON: Optional[str] = "{}"
    state: Optional[str] = "IDLE"