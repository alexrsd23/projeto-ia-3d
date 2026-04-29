from fastapi import APIRouter, HTTPException
from database import driver
from models import EntityModel, EntityUpdateModel, PositionUpdateModel, FarmerModel, RotationUpdateModel, PlotModel

# O prefixo organiza as URLs automaticamente
router = APIRouter(prefix="/api/entities", tags=["Interactions"])

@router.post("")
def create_entity(entity: EntityModel):
    query = """
    CREATE (e:Entity {
        id: $id, type: $type, posX: $posX, posY: $posY, posZ: $posZ, rotation: $rotation,
        health: $health, hunger: $hunger, name: $name,
        color: $color, sex: $sex, profession: $profession,
        trustLevel: $trustLevel, lieLevel: $lieLevel,
        married: $married, age: $age, toolHp: 100.0
    })
    RETURN e
    """
    try:
        with driver.session() as session:
            # === CORREÇÃO 1: Arredondamento para travar as casas decimais ===
            aligned_x = round(entity.position[0])
            aligned_y = round(entity.position[1], 2) # Y é altura, mantemos as casas decimais
            aligned_z = round(entity.position[2])
            
            session.run(
                query, id=entity.id, type=entity.type, 
                posX=aligned_x, posY=aligned_y, posZ=aligned_z, 
                rotation=entity.rotation,
                health=entity.health, hunger=entity.hunger, name=entity.name,
                color=entity.color, sex=entity.sex, profession=entity.profession,
                trustLevel=entity.trustLevel, lieLevel=entity.lieLevel,
                married=entity.married,
                age=entity.age
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
                    "name": node.get("name")
                })
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ROTAS DOS AGENTES SENSITIVOS (COM DNA)
# Usamos o FarmerModel pois todos têm Inventário e Memória
# ==========================================

def create_agent_query(agent_type: str):
    return f"""
    CREATE (e:Entity {{
        id: $id, type: '{agent_type}', posX: $posX, posY: $posY, posZ: $posZ,
        health: $health, hunger: $hunger, name: $name,
        color: $color, sex: $sex, profession: $profession,
        trustLevel: $trustLevel, lieLevel: $lieLevel,
        inventoryJSON: $inv, memoryJSON: $mem, state: $state,
        married: $married, age: $age
    }})
    RETURN e
    """

def execute_agent_creation(agent: FarmerModel, agent_type: str):
    try:
        with driver.session() as session:
            session.run(
                create_agent_query(agent_type), 
                id=agent.id,
                posX=agent.position[0], posY=agent.position[1], posZ=agent.position[2], 
                health=agent.health, hunger=agent.hunger, name=agent.name,
                color=agent.color, sex=agent.sex, profession=agent.profession,
                trustLevel=agent.trustLevel, lieLevel=agent.lieLevel,
                inv=agent.inventoryJSON, mem=agent.memoryJSON, state=agent.state,
                married=agent.married, age=agent.age
            )
        return {"message": f"{agent_type} criado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/farmer")
def create_farmer(farmer: FarmerModel):
    return execute_agent_creation(farmer, 'farmer')

@router.post("/woodcutter")
def create_woodcutter(woodcutter: FarmerModel):
    return execute_agent_creation(woodcutter, 'woodcutter')

@router.post("/builder")
def create_builder(builder: FarmerModel):
    return execute_agent_creation(builder, 'builder')

# ==========================================
# O "OLHO DE DEUS" (Carrega o mundo inteiro)
# ==========================================

@router.get("/survival_world")
def get_survival_entities():
    """Retorna todas as entidades, incluindo a memória, estado e DNA dos agentes."""
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
                    "rotation": node.get("rotation", 0.0),
                    "name": node.get("name"),
                    "birthdate": node.get("birthdate"),
                    "health": node.get("health"),
                    "hunger": node.get("hunger"),
                    "inventoryJSON": node.get("inventoryJSON"),
                    "memoryJSON": node.get("memoryJSON"),
                    "state": node.get("state"),
                    # === INJEÇÃO DO DNA NA LEITURA ===
                    "color": node.get("color"),
                    "sex": node.get("sex"),
                    "profession": node.get("profession"),
                    "trustLevel": node.get("trustLevel"),
                    "lieLevel": node.get("lieLevel"),
                    "married": node.get("married", False), 
                    "age": node.get("age", 0)
                })
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... (Mantenha as suas rotas PUT e DELETE originais aqui em baixo) ...
@router.delete("/{entity_id}")
def delete_entity(entity_id: str):
    query = "MATCH (e:Entity {id: $id}) DETACH DELETE e"
    try:
        with driver.session() as session:
            session.run(query, id=entity_id)
        return {"message": "Entidade apagada!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("")
def delete_all_entities():
    query = "MATCH (e:Entity) DETACH DELETE e"
    try:
        with driver.session() as session:
            session.run(query)
        return {"message": "Todas as entidades foram apagadas!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/{entity_id}/position")
def update_entity_position(entity_id: str, pos_update: PositionUpdateModel):
    query = """
    MATCH (e:Entity {id: $id})
    SET e.posX = $posX, e.posY = $posY, e.posZ = $posZ
    RETURN e
    """
    try:
        with driver.session() as session:
            # === CORREÇÃO 1: Arredondamento ao mover ===
            aligned_x = round(pos_update.position[0])
            aligned_y = round(pos_update.position[1], 2)
            aligned_z = round(pos_update.position[2])
            
            result = session.run(
                query, 
                id=entity_id, 
                posX=aligned_x, 
                posY=aligned_y, 
                posZ=aligned_z
            )
            # Solução segura: Se não encontrar no banco, avisa no log interno mas não crasha a API
            records = list(result)
            if not records:
                print(f"Aviso: Entidade {entity_id} movida na tela, mas ainda não existe no Banco.")
                
        return {"message": "Posição atualizada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.patch("/{entity_id}/rotate")
def update_entity_rotation(entity_id: str, rot_update: RotationUpdateModel):
    query = "MATCH (e:Entity {id: $id}) SET e.rotation = $rotation RETURN e"
    try:
        with driver.session() as session:
            result = session.run(query, id=entity_id, rotation=rot_update.rotation)
            
            records = list(result)
            if not records:
                print(f"Aviso: Tentativa de rotacionar entidade {entity_id} não encontrada.")
                
        return {"message": "Rotação atualizada!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/wolf")
def create_wolf(wolf: FarmerModel):
    # O Lobo usa a mesma estrutura biológica (FarmerModel) pois tem HP, Fome e Estado
    return execute_agent_creation(wolf, 'wolf')

@router.post("/plots/reserve")
def reserve_plot(plot: PlotModel):
    query = """
    MATCH (owner:Entity {id: $ownerId})
    CREATE (p:Plot {
        id: $id, 
        startX: $startX, 
        startZ: $startZ, 
        width: $width, 
        height: $height, 
        status: $status,
        createdAt: datetime()
    })
    CREATE (owner)-[:OWNS]->(p)
    RETURN p
    """
    try:
        with driver.session() as session:
            session.run(query, 
                id=plot.id, ownerId=plot.ownerId,
                startX=plot.startX, startZ=plot.startZ,
                width=plot.width, height=plot.height,
                status=plot.status
            )
        return {"message": "Espaço reservado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/plots")
def get_all_plots():
    query = "MATCH (p:Plot) RETURN p"
    plots = []
    try:
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                node = record["p"]
                plots.append({
                    "id": node["id"],
                    "ownerId": "unknown", # Opcional, pode fazer MATCH (owner)-[:OWNS]->(p) depois
                    "startX": node["startX"],
                    "startZ": node["startZ"],
                    "width": node["width"],
                    "height": node["height"],
                    "status": node["status"]
                })
        return plots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/blacksmith")
def create_blacksmith(blacksmith: FarmerModel):
    # Fix: Sobrescreve valores padrão para garantir coerência entre o Cérebro e o Banco
    blacksmith.type = 'blacksmith'
    blacksmith.profession = 'Ferreiro'
    return execute_agent_creation(blacksmith, 'blacksmith')