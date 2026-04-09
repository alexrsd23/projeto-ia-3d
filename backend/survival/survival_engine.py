import json
import random
import uuid
from survival.biology import BiologySystem
from datetime import datetime

def process_survival_tick(survival_brain, session):
    biology = BiologySystem()
    current_tick = getattr(survival_brain, 'tick_counter', 0)
    survival_brain.tick_counter = current_tick + 1

    updates_agents = []
    updates_tiles = []
    dead_agents = []
    events = []
    
    # 1. Busca Global (Agora puxa a memória e o estado)
    query_agents = "MATCH (e:Entity {type: 'farmer'}) RETURN e.id AS id, e.posX AS x, e.posZ AS z, e.health AS hp, e.hunger AS hunger, e.name AS name, e.inventoryJSON AS inventoryJSON, e.memoryJSON AS memoryJSON, e.state AS state"
    query_world = "MATCH (e:Entity) WHERE e.type <> 'farmer' RETURN e.id AS id, e.type AS type, e.posX AS x, e.posZ AS z"
    query_tiles = "MATCH (t:Tile) RETURN t.id AS id, t.gridX AS x, t.gridZ AS z, t.type AS type, t.cropsJSON AS cropsJSON"
    
    agents = session.run(query_agents).data()
    world_entities = session.run(query_world).data()
    world_tiles = session.run(query_tiles).data()
    
    tiles_map = {t['id']: t for t in world_tiles}

    for agent in agents:
        inv = survival_brain.inventory_sys.parse(agent.get('inventoryJSON', "{}"))
        
        # 2. O Cérebro Pensa e Atualiza a RAM (AGORA COM 5 VARIÁVEIS)
        action, new_x, new_z, target_id, brain_log = survival_brain.decide_next_move(agent, world_entities, world_tiles, current_tick)
        
        # Formatação Cronológica do Log do Cérebro
        current_time = datetime.now().strftime("%H:%M:%S")
        agent_name = agent.get('name', f"Agente {agent['id'][:4]}")
        
        if brain_log:
            # INFO padrão de pensamento e navegação
            events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"{agent_name} — {brain_log}", "timestamp": current_time})

        # Extração de Dados
        state_msg = survival_brain.agent_states.get(agent['id'], "IDLE")
        raw_mem = survival_brain.memory_sys.agent_memories.get(agent['id'], {})
        
        # Simplifica a memória para o formato leve que o React espera (Impede crash de tuplos no JSON)
        safe_memory = {
            "food": {f"item{i}": 1 for i in range(len(raw_mem.get('food', {})))},
            "farms": {f"item{i}": 1 for i in range(len(raw_mem.get('farms', {})))},
            "hazards": {f"item{i}": 1 for i in range(len(raw_mem.get('hazards', {})))}
        }
        
        action_type_for_bio = "MOVE" if action == "MOVE" else ("ACTION" if action in ["HARVEST", "PLANT", "PLOW"] else "IDLE")
        bio_result = biology.process_tick(agent, action_type_for_bio)
        
        new_hunger = bio_result['hunger']
        new_hp = bio_result['hp']
        
        if bio_result['is_dead']:
            dead_agents.append(agent['id'])
            events.append({"id": f"evt-{random.randint(1000,9999)}", "level": "ERROR", "message": f"☠️ {agent['name']} morreu de fome!", "timestamp": "now"})
            continue

        # 3. Execução das Ações Físicas (Logs de Sucesso/Morte)
        if action == "EAT_INVENTORY":
            if survival_brain.inventory_sys.consume_potato(inv):
                recovered = biology.consume_food({'hunger': new_hunger, 'hp': new_hp})
                new_hunger, new_hp = recovered['hunger'], recovered['hp']
                events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"{agent_name} — Inventário: Consumiu 1 batata (Nova fome: {new_hunger:.1f}%)", "timestamp": current_time})

        elif action == "HARVEST":
            tile = tiles_map.get(target_id)
            if tile and tile['cropsJSON']:
                crops = json.loads(tile['cropsJSON'])
                mature_crops = [c for c in crops if c['stage'] == 2]
                
                if mature_crops:
                    crops.remove(mature_crops[0])
                    inv = survival_brain.inventory_sys.add_harvest(inv)
                    events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"{agent_name} — Colheita concluída. Armazenou recursos na mochila.", "timestamp": current_time})
                    
                    if new_hunger < 70 and survival_brain.inventory_sys.consume_potato(inv):
                        recovered = biology.consume_food({'hunger': new_hunger, 'hp': new_hp})
                        new_hunger, new_hp = recovered['hunger'], recovered['hp']
                    
                    tile['cropsJSON'] = json.dumps(crops)
                    updates_tiles.append(tile)

        elif action == "PLOW":
            tile = tiles_map.get(target_id)
            if tile:
                tile['type'] = 'farm'
                updates_tiles.append(tile)

        elif action == "PLANT":
            tile = tiles_map.get(target_id)
            if tile and survival_brain.inventory_sys.consume_seed(inv):
                crops = json.loads(tile['cropsJSON']) if tile.get('cropsJSON') else []
                if len(crops) < 2:
                    offset = [-0.5, -0.5] if len(crops) == 0 else [0.5, 0.5]
                    crops.append({"id": str(uuid.uuid4()), "type": "potato", "stage": 0, "positionOffset": offset})
                    tile['cropsJSON'] = json.dumps(crops)
                    updates_tiles.append(tile)

        # Adiciona a memória e estado ao pacote de atualização
        updates_agents.append({
            "id": agent['id'], "x": new_x, "z": new_z, 
            "hp": new_hp, "hunger": new_hunger,
            "inv": survival_brain.inventory_sys.to_string(inv),
            "mem": json.dumps(safe_memory),
            "state": state_msg
        })
        
    # =====================================================================
    # NOVO: Biologia do Mundo (Crescimento das Batatas)
    # =====================================================================
    for tile_id, tile in tiles_map.items():
        if not tile.get('cropsJSON') or tile.get('type') != 'farm':
            continue
            
        crops = json.loads(tile['cropsJSON'])
        changed = False
        for crop in crops:
            # === NOVO TEMPO AGRÍCOLA (2% de chance) ===
            # A planta demora agora, em média, 100 ticks a amadurecer.
            # O agente perde apenas 10% de fome durante este tempo!
            if crop['stage'] < 2 and random.random() < 0.02: 
                crop['stage'] += 1
                changed = True
                
        if changed:
            tile['cropsJSON'] = json.dumps(crops)
            # Evita duplicar a gravação se um agente acabou de plantar/colher neste mesmo tick
            if tile not in updates_tiles:
                updates_tiles.append(tile)

    # 4. Gravações no Neo4j
    if dead_agents:
        session.run("MATCH (e:Entity) WHERE e.id IN $ids DETACH DELETE e", ids=dead_agents)
        
    if updates_agents:
        session.run("""
        UNWIND $updates AS up
        MATCH (e:Entity {id: up.id})
        SET e.posX = up.x, e.posZ = up.z, e.health = up.hp, e.hunger = up.hunger, e.inventoryJSON = up.inv, e.memoryJSON = up.mem, e.state = up.state
        """, updates=updates_agents)
        
    if updates_tiles:
        session.run("""
        UNWIND $updates AS up
        MATCH (t:Tile {id: up.id})
        SET t.type = up.type, t.cropsJSON = up.cropsJSON
        """, updates=updates_tiles)

    return {
        "message": "Tick Biológico processado",
        "events": events,
        "heatmap": [], 
        "lastAction": 0,
        "qValues": [0]*8, 
        "currentState": [0,0,0],
        "analytics": None
    }