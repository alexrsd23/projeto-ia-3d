from fastapi import APIRouter, HTTPException
from database import driver
from models import EntityModel, EntityUpdateModel, PositionUpdateModel, FarmerModel

# O prefixo organiza as URLs automaticamente
router = APIRouter(prefix="/api/entities", tags=["Interactions"])

@router.post("")
def create_entity(entity: EntityModel):
    query = """
    CREATE (e:Entity {
        id: $id, type: $type, posX: $posX, posY: $posY, posZ: $posZ,
        health: $health, hunger: $hunger, name: $name
    })
    RETURN e
    """
    try:
        with driver.session() as session:
            session.run(
                query, id=entity.id, type=entity.type, 
                posX=entity.position[0], posY=entity.position[1], posZ=entity.position[2], 
                health=entity.health, hunger=entity.hunger, name=entity.name
            )
        return {"message": f"{entity.type} criado com sucesso no Neo4j!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
def get_entities():
    query = "MATCH (e:Entity) RETURN e"
    entities = []
    try:
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                node = record["e"]
                entities.append({
                    "id": node["id"],
                    "type": node["type"],
                    "position": [node["posX"], node["posY"], node["posZ"]],
                    "name": node.get("name"),
                    "birthdate": node.get("birthdate"),
                    "health": node.get("health"),
                    "hunger": node.get("hunger")
                })
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{entity_id}")
def update_entity_identity(entity_id: str, data: EntityUpdateModel):
    query = "MATCH (e:Entity {id: $id}) SET e.name = $name, e.birthdate = $birthdate RETURN e"
    try:
        with driver.session() as session:
            session.run(query, id=entity_id, name=data.name, birthdate=data.birthdate)
        return {"message": "Identidade atualizada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{entity_id}/position")
def update_entity_position(entity_id: str, data: PositionUpdateModel):
    query = "MATCH (e:Entity {id: $id}) SET e.posX = $x, e.posY = $y, e.posZ = $z RETURN e"
    try:
        with driver.session() as session:
            session.run(query, id=entity_id, x=data.position[0], y=data.position[1], z=data.position[2])
        return {"message": "Posição salva!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# =====================================================================
# MODO SOBREVIVÊNCIA: Rotas exclusivas para não afetar o sistema de rotas
# =====================================================================
@router.post("/farmer")
def create_farmer(farmer: FarmerModel):
    query = """
    CREATE (e:Entity {
        id: $id, type: 'farmer', posX: $posX, posY: $posY, posZ: $posZ,
        health: $health, hunger: $hunger, name: $name, 
        inventoryJSON: $inv, memoryJSON: $mem, state: $state
    })
    RETURN e
    """
    try:
        with driver.session() as session:
            session.run(
                query, id=farmer.id, 
                posX=farmer.position[0], posY=farmer.position[1], posZ=farmer.position[2], 
                health=farmer.health, hunger=farmer.hunger, name=farmer.name,
                inv=farmer.inventoryJSON, mem=farmer.memoryJSON, state=farmer.state
            )
        return {"message": "Fazendeiro criado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/survival_world")
def get_survival_entities():
    """Nova Rota GET: Retorna todas as entidades, incluindo a memória e estado dos fazendeiros."""
    query = "MATCH (e:Entity) RETURN e"
    entities = []
    try:
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                node = record["e"]
                entities.append({
                    "id": node["id"],
                    "type": node["type"],
                    "position": [node["posX"], node["posY"], node["posZ"]],
                    "name": node.get("name"),
                    "birthdate": node.get("birthdate"),
                    "health": node.get("health"),
                    "hunger": node.get("hunger"),
                    "inventoryJSON": node.get("inventoryJSON"),
                    "memoryJSON": node.get("memoryJSON"),
                    "state": node.get("state")
                })
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))