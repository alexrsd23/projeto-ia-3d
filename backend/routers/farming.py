from fastapi import APIRouter, HTTPException
import json
from database import driver
from models import TileModel

router = APIRouter(prefix="/api/tiles", tags=["Farming"])

@router.post("")
def save_tile(tile: TileModel):
    query = """
    MERGE (t:Tile {id: $id})
    SET t.gridX = $gridX, t.gridZ = $gridZ, t.type = $type, t.cropsJSON = $cropsJSON
    RETURN t
    """
    try:
        with driver.session() as session:
            session.run(query, id=tile.id, gridX=tile.gridX, gridZ=tile.gridZ, type=tile.type, cropsJSON=json.dumps(tile.crops))
        return {"message": "Fazenda atualizada!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
def get_tiles():
    query = "MATCH (t:Tile) RETURN t"
    tiles = []
    try:
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                node = record["t"]
                tiles.append({
                    "id": node["id"],
                    "gridX": node["gridX"],
                    "gridZ": node["gridZ"],
                    "type": node["type"],
                    "crops": json.loads(node["cropsJSON"]) if node.get("cropsJSON") else []
                })
        return tiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))