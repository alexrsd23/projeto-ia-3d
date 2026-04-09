# backend/survival/survival_engine.py
import math
import random
from models import EntityModel # Suas tipagens do Pydantic

def process_survival_tick(survival_brain, session):
    updates_positions = []
    updates_vitals = []
    dead_agents = []
    events = []
    
    # 1. BUSCA O ESTADO DO MUNDO (Visão local)
    query = "MATCH (e:Entity) RETURN e.id AS id, e.type AS type, e.posX AS x, e.posZ AS z, e.health AS hp, e.hunger AS hunger, e.name AS name"
    world_data = session.run(query).data()
    
    agents = [e for e in world_data if e['type'] == 'character']
    hazards = [e for e in world_data if e['type'] == 'cactus']
    # Aqui você buscaria as batatas do farm também
    
    for agent in agents:
        # 2. DEGRADAÇÃO BIOLÓGICA
        # Exemplo: perde 1 de fome a cada tick
        new_hunger = max(0, agent.get('hunger', 100) - 1)
        new_hp = agent.get('hp', 100)
        
        if new_hunger == 0:
            new_hp -= 5 # Começa a morrer de inanição
            
        if new_hp <= 0:
            dead_agents.append(agent['id'])
            events.append({"id": f"evt-{random.randint(1000,9999)}", "level": "ERROR", "message": f"☠️ {agent['name']} morreu de fome!", "timestamp": "now"})
            continue
            
        # 3. CONSULTA O CÉREBRO DE SOBREVIVÊNCIA
        # Passamos a posição dele e o que tem em volta
        new_x, new_z, action_log = survival_brain.decide_next_move(agent, hazards)
        
        # 4. RESOLVE A FÍSICA E COLISÕES
        # (Lógica de colidir com cacto ou comer batata entra aqui)
        
        # Prepara para salvar no Neo4j
        updates_positions.append({"id": agent['id'], "x": new_x, "z": new_z})
        updates_vitals.append({"id": agent['id'], "hp": new_hp, "hunger": new_hunger})

    # 5. ATUALIZA O BANCO DE DADOS EM LOTE
    if dead_agents:
        session.run("MATCH (e:Entity) WHERE e.id IN $ids DETACH DELETE e", ids=dead_agents)
        
    if updates_vitals:
        session.run("""
        UNWIND $updates AS up
        MATCH (e:Entity {id: up.id})
        SET e.health = up.hp, e.hunger = up.hunger
        """, updates=updates_vitals)
        
    if updates_positions:
        session.run("""
        UNWIND $updates AS up
        MATCH (e:Entity {id: up.id})
        SET e.posX = up.x, e.posZ = up.z
        """, updates=updates_positions)

    # 6. RETORNA O PAYLOAD PARA O REACT
    return {
        "message": "Tick de Sobrevivência processado",
        "events": events,
        "heatmap": [], # Pode desativar o heatmap neste modo se preferir
        "lastAction": 0,
        "qValues": [0]*8, 
        "currentState": [0,0,0],
        "analytics": None # Sem rotas ótimas neste modo
    }