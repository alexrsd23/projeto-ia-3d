import math
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neo4j import GraphDatabase
from typing import Optional

# 1. Configuração do Servidor
app = FastAPI(title="Mundo IA - Backend")

# Liberando o CORS para o React conseguir fazer as requisições
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configuração do Banco de Dados
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "admin123" # <-- NÃO ESQUEÇA DE COLOCAR SUA SENHA DO NEO4J AQUI!
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# 3. O "Contrato" de Dados
class EntityModel(BaseModel):
    id: str
    type: str
    position: list[float]
    # Tornando opcionais para não quebrar os que já existem
    name: Optional[str] = None
    birthdate: Optional[str] = None

class EntityUpdateModel(BaseModel):
    name: str
    birthdate: str

class PositionUpdateModel(BaseModel):
    position: list[float]

# 4. As Rotas (Endpoints)
@app.get("/")
def home():
    return {"status": "Servidor do Mundo IA está online no Python 3.12!"}

@app.post("/api/entities")
def create_entity(entity: EntityModel):
    """Grava um novo boneco ou casa no banco de grafos Neo4j"""
    
    query = """
    CREATE (e:Entity {
        id: $id, 
        type: $type, 
        posX: $posX, 
        posY: $posY, 
        posZ: $posZ
    })
    RETURN e
    """
    
    try:
        with driver.session() as session:
            session.run(
                query, 
                id=entity.id, 
                type=entity.type, 
                posX=entity.position[0], 
                posY=entity.position[1], 
                posZ=entity.position[2]
            )
        return {"message": f"{entity.type} criado com sucesso no Neo4j!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities")
def get_entities():
    """Lê todo o estado atual do mundo no Neo4j e envia para o Frontend"""
    
    # Busca todos os nós do tipo Entity
    query = "MATCH (e:Entity) RETURN e"
    
    entities = []
    try:
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                node = record["e"] # Pega o nó retornado pelo Neo4j
                # Monta o dicionário no mesmo formato que o React espera
                entities.append({
                    "id": node["id"],
                    "type": node["type"],
                    "position": [node["posX"], node["posY"], node["posZ"]],
                    "name": node.get("name"),           # Novo
                    "birthdate": node.get("birthdate")  # Novo
                })
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tick")
def simulate_tick():
    """Avança o tempo validando colisões antes de mover"""
    
    # 1. Busca todos no banco para o Python analisar
    query_get = "MATCH (e:Entity) RETURN e.id AS id, e.type AS type, e.posX AS x, e.posZ AS z"
    
    try:
        with driver.session() as session:
            results = session.run(query_get).data()
            
            characters = [r for r in results if r['type'] == 'character']
            obstacles = results # Todos são obstáculos (casas e outros personagens)
            
            updates = []
            
            for char in characters:
                # O boneco "pensa" em um novo movimento
                dx = (random.random() * 2 - 1) * 0.5
                dz = (random.random() * 2 - 1) * 0.5
                new_x = char['x'] + dx
                new_z = char['z'] + dz

                new_x = max(-24.5, min(24.5, new_x))
                new_z = max(-24.5, min(24.5, new_z))
                
                collision = False
                char_radius = 0.5
                
                # Verifica se essa nova posição bate em alguém
                for obs in obstacles:
                    if char['id'] == obs['id']:
                        continue # Não colide com ele mesmo
                        
                    # Raio de colisão (0.5 para pessoa, 1.0 para casa)
                    obs_radius = 0.5 if obs['type'] == 'character' else 1.0 
                    
                    # Teorema de Pitágoras para calcular a distância no chão (X e Z)
                    dist = math.sqrt((new_x - obs['x'])**2 + (new_z - obs['z'])**2)
                    min_dist = char_radius + obs_radius
                    
                    if dist < min_dist:
                        collision = True
                        break # Bateu! Interrompe a verificação.
                
                # Se não bateu em nada, autorizamos o movimento
                if not collision:
                    updates.append({"id": char['id'], "x": new_x, "z": new_z})
                    
                    # Atualiza a posição na memória do loop atual para que o próximo 
                    # boneco da fila não ande para onde este acabou de ir
                    char['x'] = new_x
                    char['z'] = new_z

            # 2. Salva as novas posições validadas no Neo4j de uma só vez
            if updates:
                query_update = """
                UNWIND $updates AS update
                MATCH (c:Entity {id: update.id})
                SET c.posX = update.x, c.posZ = update.z
                """
                session.run(query_update, updates=updates)
                
        return {"message": f"Tick executado. {len(updates)} se moveram sem colidir."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/entities/{entity_id}")
def update_entity_identity(entity_id: str, data: EntityUpdateModel):
    """Atualiza o nome e data de nascimento de um boneco específico"""
    query = """
    MATCH (e:Entity {id: $id})
    SET e.name = $name, e.birthdate = $birthdate
    RETURN e
    """
    try:
        with driver.session() as session:
            session.run(query, id=entity_id, name=data.name, birthdate=data.birthdate)
        return {"message": "Identidade atualizada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/entities/{entity_id}/position")
def update_entity_position(entity_id: str, data: PositionUpdateModel):
    """Atualiza as coordenadas X e Z de um objeto após ser arrastado"""
    query = """
    MATCH (e:Entity {id: $id})
    SET e.posX = $x, e.posY = $y, e.posZ = $z
    RETURN e
    """
    try:
        with driver.session() as session:
            session.run(query, id=entity_id, x=data.position[0], y=data.position[1], z=data.position[2])
        return {"message": "Posição salva com sucesso no banco de dados!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))