from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class EntityModel(BaseModel):
    id: str
    type: str
    position: list[float]
    rotation: Optional[float] = 0.0
    name: Optional[str] = None
    birthdate: Optional[str] = None
    health: Optional[int] = None
    hunger: Optional[int] = None
    color: Optional[str] = None
    sex: Optional[str] = None
    profession: Optional[str] = None
    trustLevel: Optional[float] = None
    lieLevel: Optional[float] = None

class EntityUpdateModel(BaseModel):
    name: str
    birthdate: str

class PositionUpdateModel(BaseModel):
    position: list[float]
    
class RotationUpdateModel(BaseModel):
    rotation: float

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