import json
import random
import uuid
from survival.biology import BiologySystem
from datetime import datetime
from survival.economy_system import EconomySystem
from survival.forestry_system import ForestrySystem

def process_survival_tick(survival_brain, session):
    economy = EconomySystem()
    biology = BiologySystem()
    EconomySystem.cool_down_market()
    current_tick = getattr(survival_brain, 'tick_counter', 0)
    survival_brain.tick_counter = current_tick + 1

    updates_agents = []
    updates_tiles = []
    dead_agents = []
    events = []
    new_entities_to_create = []
    
    locked_targets = set()
    
    # Tipos de agentes inteligentes/sensitivos do sistema
    AGENT_TYPES = ['farmer', 'woodcutter', 'builder', 'wolf']

    # 1. Busca global de agentes sensíveis (Agora verifica Propriedades!)
    query_agents = """
    MATCH (e:Entity)
    WHERE e.type IN $agent_types
    // OPTIONAL MATCH verifica se ele é dono de um Plot. Se for, p.id existe.
    OPTIONAL MATCH (e)-[:OWNS]->(p:Plot)
    RETURN 
        e.id AS id,
        e.type AS type,
        e.posX AS x,
        e.posZ AS z,
        e.health AS hp,
        e.hunger AS hunger,
        e.name AS name,
        e.inventoryJSON AS inventoryJSON,
        e.memoryJSON AS memoryJSON,
        e.state AS state,
        coalesce(e.married, false) AS married,
        coalesce(e.age, 0) AS age,
        coalesce(e.sex, 'M') AS sex,
        // Retorna TRUE se o p.id não for nulo (ou seja, se ele encontrou o relacionamento OWNS)
        (p.id IS NOT NULL) AS owns_plot
    """

    # 2. Busca de tudo que NÃO é agente sensível
    query_world = """
    MATCH (e:Entity)
    WHERE NOT e.type IN $agent_types
    RETURN 
        e.id AS id,
        e.type AS type,
        e.posX AS x,
        e.posZ AS z,
        coalesce(e.health, 100.0) AS hp,
        coalesce(e.age, 0) AS age
    """

    # === ADICIONE ESTA QUERY QUE ESTAVA FALTANDO ===
    query_tiles = """
    MATCH (t:Tile) 
    RETURN 
        t.id AS id, 
        t.gridX AS x, 
        t.gridZ AS z, 
        t.type AS type, 
        t.cropsJSON AS cropsJSON
    """

    # === NOVO: BUSCA DAS PROPRIEDADES RESERVADAS (AGORA COM O ID DO DONO) ===
    query_plots = """
    MATCH (p:Plot)
    OPTIONAL MATCH (owner:Entity)-[:OWNS]->(p)
    RETURN p.id AS id, p.startX AS startX, p.startZ AS startZ, p.width AS width, p.height AS height, p.status AS status, owner.id AS ownerId
    """

    # Execução das Queries no Banco de Dados
    agents = session.run(query_agents, agent_types=AGENT_TYPES).data()
    world_entities = session.run(query_world, agent_types=AGENT_TYPES).data()
    world_tiles = session.run(query_tiles).data()
    world_plots = session.run(query_plots).data() # <--- ADICIONE A EXECUÇÃO AQUI
    
    tiles_map = {t['id']: t for t in world_tiles}
    
    # =====================================================================
    # NOVO: Biologia do Mundo e Depreciação (Entropia Estrutural)
    # =====================================================================
    for entity in world_entities:
        if entity['type'] == 'fence':
            # 0.5% de chance da cerca quebrar a cada tick
            if random.random() < 0.0002:
                updates_agents.append({
                    "id": entity['id'], "type": "damaged_fence", 
                    "x": entity['x'], "z": entity['z'],
                    # === ADICIONE ISTO AQUI ===
                    "hp": 0, "hunger": 0, "inv": "{}", "mem": "{}", "state": "IDLE"
                })

    for agent in agents:
        inv = survival_brain.inventory_sys.parse(agent.get('inventoryJSON', "{}"))
        
        # === CORREÇÃO 1: Restaura a Memória real do Neo4j para a RAM ===
        if agent.get('memoryJSON') and agent['memoryJSON'] != "{}":
            survival_brain.memory_sys.load_from_db(agent['id'], agent['memoryJSON'])
        
        # 2. O Cérebro Pensa e Atualiza a RAM
        action, new_x, new_z, target_id, brain_log = survival_brain.decide_next_move(
            agent, world_entities, world_tiles, world_plots, current_tick, agents
        )
        
        # (Mantenha o código de log do current_time e agent_name igual...)
        current_time = datetime.now().strftime("%H:%M:%S")
        agent_name = agent.get('name')
        if not agent_name:
            agent_name = f"Lobo {agent['id'][:4]}" if agent['type'] == 'wolf' else f"Agente {agent['id'][:4]}"
        if brain_log:
            events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"{agent_name} — {brain_log}", "timestamp": current_time})

        state_msg = survival_brain.agent_states.get(agent['id'], "IDLE")
        raw_mem = survival_brain.memory_sys.agent_memories.get(agent['id'], {})
        
        # === CORREÇÃO 2: PERSISTÊNCIA REAL NO BANCO ===
        # Salvamos as coordenadas reais convertendo a tupla (x,z) em string "x,z"
        safe_memory = {
            "food": {f"{k[0]},{k[1]}": v for k, v in raw_mem.get('food', {}).items()},
            "farms": {f"{k[0]},{k[1]}": v for k, v in raw_mem.get('farms', {}).items()},
            "hazards": {f"{k[0]},{k[1]}": v for k, v in raw_mem.get('hazards', {}).items()},
            "rejections": raw_mem.get('rejections', [])
        }
        
        action_type_for_bio = "MOVE" if action == "MOVE" else ("ACTION" if action in ["HARVEST", "PLANT", "PLOW"] else "IDLE")
        
        # === DESGASTE BIOLÓGICO E VELHICE ===
        bio_status = biology.process_tick(agent, action_type_for_bio)
        new_hunger = bio_status['hunger']
        new_hp = bio_status['hp']
        agent['age'] = bio_status['age'] # O agente ficou 1 tick mais velho
        
        # === A NOVA LÓGICA DA MORTE (Metamorfose para Loot) ===
        if bio_status['is_dead']:
            # Log emocional para o Terminal
            if bio_status.get('death_reason') == "OLD_AGE":
                events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"⚰️ FALECIMENTO: {agent_name} faleceu pacificamente de velhice aos {agent['age']} ciclos. Uma vida completa.", "timestamp": current_time})
            else:
                events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"☠️ MORTE: {agent_name} sucumbiu à fome...", "timestamp": current_time})
            
            updates_agents.append({
                "id": agent['id'], 
                "type": "loot",  
                "x": new_x, "z": new_z, 
                "hp": 0.0, "hunger": 0.0,
                "age": agent['age'], # <--- Guardamos a idade em que faleceu
                "inv": survival_brain.inventory_sys.to_string(inv), 
                "mem": json.dumps(safe_memory),
                "state": "DEAD"
            })
            continue # Pula as ações físicas

        # 3. Execução das Ações Físicas (Logs de Sucesso/Morte)
        
        # === NOVO: AVALIAÇÃO DE CONCORRÊNCIA ===
        # Se a ação interage com um alvo externo, verificamos se ele já foi bloqueado
        if action not in ["IDLE", "MOVE", "EAT_INVENTORY", "CRAFT_FENCE", "PROPOSE_MARRIAGE", "RESERVE_PLOT"]:
            t_id = target_id["id"] if isinstance(target_id, dict) else target_id
            if t_id:
                if t_id in locked_targets:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"⏳ {agent_name} hesitou! Outro agente interagiu com o alvo primeiro.", "timestamp": current_time})
                    continue # Aborta a ação física e passa para o próximo agente
                else:
                    locked_targets.add(t_id) # Tranca o alvo para o resto deste tick!
        
        if action == "EAT_INVENTORY":
            if survival_brain.inventory_sys.consume_potato(inv):
                recovered = biology.consume_food({'hunger': new_hunger, 'hp': new_hp})
                new_hunger, new_hp = recovered['hunger'], recovered['hp']
                events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"{agent_name} — Inventário: Consumiu 1 batata (Nova fome: {new_hunger:.1f}%)", "timestamp": current_time})
                
        elif action == "ATTACK_AGENT":
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent:
                # O lobo arranca 20 pontos de Vida!
                target_agent['hp'] = target_agent.get('hp', 100.0) - 20.0
                events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"🩸 {agent_name} cravou os dentes em {target_agent.get('name', 'Alguém')}! (-20 HP)", "timestamp": current_time})
                
                for up in updates_agents:
                    if up['id'] == target_id:
                        up['hp'] = target_agent['hp']
                        up['state'] = "BLEEDING"
                        if target_agent['hp'] <= 0:
                            up['type'] = 'loot'
                            up['state'] = 'DEAD'
                            
                            # === NOVO: O LOBO ALIMENTA-SE ===
                            new_hunger = 100.0 # Barriga cheia
                            new_hp = 100.0     # Vida cheia
                            events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"🐺 CARNIFICINA: {agent_name} devorou a presa e está 100% saciado!", "timestamp": current_time})

        elif action == "ATTACK_FENCE":
            target_entity = next((e for e in world_entities if e['id'] == target_id), None)
            if target_entity:
                current_hp = float(target_entity.get('hp', 100.0))
                
                # === CORREÇÃO: Variável isolada (fence_new_hp) para não matar o lobo! ===
                fence_new_hp = current_hp - 35.0 
                
                if fence_new_hp <= 0:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🐾 {agent_name} destruiu a cerca aos pedaços!", "timestamp": current_time})
                    updates_agents.append({"id": target_id, "type": "damaged_fence", "x": target_entity['x'], "z": target_entity['z'], "hp": 0, "hunger": 0, "age": target_entity.get('age', 0), "inv": "{}", "mem": "{}", "state": "IDLE"})
                    world_entities = [e for e in world_entities if e['id'] != target_id]
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🐺 {agent_name} está a morder a cerca! (Integridade: {fence_new_hp:.0f}/100)", "timestamp": current_time})
                    target_entity['hp'] = fence_new_hp
                    updates_agents.append({"id": target_id, "type": "fence", "x": target_entity['x'], "z": target_entity['z'], "hp": fence_new_hp, "hunger": 0, "age": target_entity.get('age', 0), "inv": "{}", "mem": "{}", "state": "IDLE"})
                    world_entities = [e for e in world_entities if e['id'] != target_id]
                
        # === O MOTOR DE CASAMENTO (SOCIOLOGIA & GENÉTICA) ===
        elif action == "PROPOSE_MARRIAGE":
            agent_a = agent['id']
            agent_b = target_id
            
            if agent_a < agent_b: 
                try:
                    # 1. VALIDAÇÃO DE CONSANGUINIDADE (TABU GENÉTICO)
                    query_incest = """
                    MATCH (a:Entity {id: $idA}), (b:Entity {id: $idB})
                    // Padrão 1 e 2: Ascendentes ou Descendentes diretos (infinito)
                    OPTIONAL MATCH p1=(a)-[:PARENT_OF*1..]->(b)
                    OPTIONAL MATCH p2=(b)-[:PARENT_OF*1..]->(a)
                    // Padrão 3: Irmãos (partilham um parente que aponta para os dois)
                    OPTIONAL MATCH p3=(a)<-[:PARENT_OF]-()-[:PARENT_OF]->(b)
                    // Padrão 4 e 5: Tio(a) e Sobrinho(a)
                    OPTIONAL MATCH p4=(a)<-[:PARENT_OF]-()-[:PARENT_OF]-()-[:PARENT_OF]->(b)
                    OPTIONAL MATCH p5=(b)<-[:PARENT_OF]-()-[:PARENT_OF]-()-[:PARENT_OF]->(a)
                    // Se qualquer um dos caminhos existir, é incesto
                    RETURN (p1 IS NOT NULL OR p2 IS NOT NULL OR p3 IS NOT NULL OR p4 IS NOT NULL OR p5 IS NOT NULL) AS is_incest
                    """
                    incest_check = session.run(query_incest, idA=agent_a, idB=agent_b).single()
                    
                    if incest_check and incest_check["is_incest"]:
                        # A Natureza interveio!
                        events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"🧬 TABU GENÉTICO: A biologia impediu o flerte! {agent_name} e o alvo são parentes próximos.", "timestamp": current_time})
                        
                        # Grava na memória dos DOIS para eles nunca mais tentarem o absurdo
                        survival_brain.memory_sys._ensure_agent(agent_a)
                        survival_brain.memory_sys._ensure_agent(agent_b)
                        survival_brain.memory_sys.agent_memories[agent_a]['rejections'].append(agent_b)
                        survival_brain.memory_sys.agent_memories[agent_b]['rejections'].append(agent_a)
                        continue # Aborta a ação deste tick
                    
                    # 2. SE A GENÉTICA PERMITIR, EXECUTA O CASAMENTO:
                    query_marry = """
                    MATCH (a:Entity {id: $idA}), (b:Entity {id: $idB})
                    WHERE coalesce(a.married, false) = false AND coalesce(b.married, false) = false AND a.type = b.type
                    MERGE (a)-[r:MARRIED_TO]-(b)
                    SET a.married = true, b.married = true
                    RETURN a.name AS nameA, b.name AS nameB
                    """
                    result = session.run(query_marry, idA=agent_a, idB=agent_b).data()
                    
                    if result:
                        name_a = result[0]['nameA']
                        name_b = result[0]['nameB']
                        events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"💍 CASAMENTO: {name_a} e {name_b} casaram-se no meio da simulação!", "timestamp": current_time})
                        for a in agents:
                            if a['id'] == agent_a or a['id'] == agent_b:
                                a['married'] = True
                                
                except Exception as e:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"💔 Erro no banco durante o casamento: {str(e)}", "timestamp": current_time})
        
        # === A FASE 3: O MILAGRE DA VIDA E A ÁRVORE GENEALÓGICA ===
        elif action == "PROCREATE":
            agent_a_id = agent['id']
            agent_b_id = target_id
            
            if agent_a_id < agent_b_id: # Garante que só o parceiro A paga a conta e gera o filho
                partner = next((a for a in agents if a['id'] == agent_b_id), None)
                if partner:
                    p_inv = survival_brain.inventory_sys.parse(partner.get('inventoryJSON', "{}"))
                    a_type = agent['type']
                    
                    # 1. VALIDAÇÃO DE PAGAMENTO: Ambos precisam ter o recurso para pagar a sua metade!
                    both_can_afford = False
                    if a_type == 'farmer' and inv.get('potatoes', 0) >= 2 and p_inv.get('potatoes', 0) >= 2:
                        inv['potatoes'] -= 2
                        p_inv['potatoes'] -= 2
                        both_can_afford = True
                    elif a_type == 'woodcutter' and inv.get('logs', 0) >= 5 and p_inv.get('logs', 0) >= 5:
                        inv['logs'] -= 5
                        p_inv['logs'] -= 5
                        both_can_afford = True
                    elif a_type == 'builder' and inv.get('stones', 0) >= 5 and p_inv.get('stones', 0) >= 5:
                        inv['stones'] -= 5
                        p_inv['stones'] -= 5
                        both_can_afford = True
                        
                    if both_can_afford:
                        # 2. O CUSTO BIOLÓGICO: Ter um filho consome 25% da barra de fome de ambos!
                        new_hunger = max(0, new_hunger - 25.0)
                        partner['hunger'] = max(0, float(partner.get('hunger', 100)) - 25.0)
                        
                        # Atualiza o inventário do parceiro na RAM e no objeto de gravação
                        partner['inventoryJSON'] = survival_brain.inventory_sys.to_string(p_inv)
                        for up in updates_agents:
                            if up['id'] == agent_b_id:
                                up['hunger'] = partner['hunger']
                                up['inv'] = partner['inventoryJSON']
                                
                        # 3. MISTURA DE DNA (MENDEL 2.0)
                        child_dna = biology.mix_dna(agent, partner)
                        child_id = str(uuid.uuid4())
                        child_name = f"{child_dna['profession']} {child_id[:2].upper()}"
                        
                        try:
                            # 4. CRIAÇÃO NO NEO4J (O Alicerce da Árvore Genealógica!)
                            query_birth = """
                            MATCH (mom:Entity {id: $mom_id}), (dad:Entity {id: $dad_id})
                            CREATE (child:Entity {
                                id: $c_id, type: $c_type, posX: $c_x, posY: 0.5, posZ: $c_z,
                                health: 100.0, hunger: 100.0, name: $c_name,
                                color: $color, sex: $sex, profession: $prof,
                                trustLevel: $trust, lieLevel: $lie, married: false, age: 0,
                                inventoryJSON: "{}", memoryJSON: "{}", state: "IDLE"
                            })
                            // Cria as setas de parentesco para a nossa futura UI ler!
                            CREATE (mom)-[:PARENT_OF]->(child)
                            CREATE (dad)-[:PARENT_OF]->(child)
                            CREATE (child)-[:CHILD_OF]->(mom)
                            CREATE (child)-[:CHILD_OF]->(dad)
                            RETURN child.id
                            """
                            session.run(query_birth, 
                                mom_id=agent_a_id, dad_id=agent_b_id,
                                c_id=child_id, c_type=agent['type'], 
                                c_x=new_x, c_z=new_z, c_name=child_name,
                                color=child_dna['color'], sex=child_dna['sex'], prof=child_dna['profession'],
                                trust=child_dna['trustLevel'], lie=child_dna['lieLevel']
                            )
                            events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"👶 MILAGRE DA VIDA: {agent_name} e {partner.get('name')} tiveram um filho! Bem-vindo(a) {child_name}!", "timestamp": current_time})
                        except Exception as e:
                            events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"Erro no parto: {str(e)}", "timestamp": current_time})
                    else:
                        events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🚫 Tentativa de gravidez falhou: {agent_name} ou parceiro não têm os recursos materiais exigidos!", "timestamp": current_time})

        elif action == "RESERVE_PLOT":
            blueprint = target_id # O blueprint foi passado no parâmetro target_id
            plot_id = f"plot-{agent['id']}"
            
            # Grava no banco de dados imediatamente (Locking)
            session.run("""
            MATCH (owner:Entity {id: $ownerId})
            CREATE (p:Plot {
                id: $id, startX: $startX, startZ: $startZ, 
                width: $width, height: $height, status: "planned"
            })
            CREATE (owner)-[:OWNS]->(p)
            """, ownerId=agent['id'], id=plot_id, startX=blueprint['startX'], 
                 startZ=blueprint['startZ'], width=blueprint['width'], height=blueprint['height'])
            
            # Guarda a planta na memória do agente para ele saber o que construir
            safe_memory['my_blueprint'] = blueprint
            
            # === CORREÇÃO CRÍTICA 2: Sincronização Intra-Tick ===
            # Atualiza a lista em memória imediatamente para que os próximos agentes processados 
            # neste MESMO tick vejam o terreno e respeitem a restrição do perímetro.
            world_plots.append({
                "id": plot_id,
                "ownerId": agent['id'],
                "startX": blueprint['startX'],
                "startZ": blueprint['startZ'],
                "width": blueprint['width'],
                "height": blueprint['height'],
                "status": "planned"
            })
            
            events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"📜 {agent_name} obteve a escritura do terreno!", "timestamp": current_time})
        
        elif action == "HARVEST":
            t_id = target_id["id"] if isinstance(target_id, dict) else target_id
            tile = tiles_map.get(t_id)
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
            t_id = target_id["id"] if isinstance(target_id, dict) else target_id
            tile = tiles_map.get(t_id)
            if not tile:
                # O segredo: Cria o bloco na memória da engine para ele ser salvo no Neo4j a seguir!
                tx, tz = target_id["x"], target_id["z"]
                tile = {"id": t_id, "x": tx, "z": tz, "type": "grass", "cropsJSON": "[]"}
                tiles_map[t_id] = tile

            tile['type'] = 'farm'
            if tile not in updates_tiles:
                updates_tiles.append(tile)

        elif action == "PLANT":
            t_id = target_id["id"] if isinstance(target_id, dict) else target_id
            tile = tiles_map.get(t_id)
            if tile and survival_brain.inventory_sys.consume_seed(inv):
                crops = json.loads(tile['cropsJSON']) if tile.get('cropsJSON') else []
                if len(crops) < 2:
                    offset = [-0.5, -0.5] if len(crops) == 0 else [0.5, 0.5]
                    crops.append({"id": str(uuid.uuid4()), "type": "potato", "stage": 0, "positionOffset": offset})
                    tile['cropsJSON'] = json.dumps(crops)
                    if tile not in updates_tiles:
                        updates_tiles.append(tile)
                    
        elif action == "LOOT":
            target_entity = next((e for e in world_entities if e['id'] == target_id), None)
            if target_entity:
                # O Saco de Loot tem uma mochila virtual
                loot_inv = survival_brain.inventory_sys.parse(target_entity.get('inventoryJSON', "{}"))
                
                # Transfere tudo para o agente vivo
                inv['plobs'] = inv.get('plobs', 0.0) + loot_inv.get('plobs', 0.0)
                inv['potatoes'] = inv.get('potatoes', 0) + loot_inv.get('potatoes', 0)
                
                events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"💰 {agent_name} recolheu {loot_inv.get('plobs', 0.0)} Plobs de um espólio!", "timestamp": current_time})
                
                # Marca o saco de loot para ser deletado do banco de dados
                dead_agents.append(target_id)
                # Remove da memória visual para não tentarem saquear de novo neste tick
                world_entities = [e for e in world_entities if e['id'] != target_id]

        elif action == "CHOP_TREE":
            target_entity = next((e for e in world_entities if e['id'] == target_id), None)
            if target_entity:
                # Chama a física que você criou no novo arquivo!
                stump_update, dropped_logs, evt = ForestrySystem.process_chopping(target_entity, current_time, agent_name)
                
                events.append(evt)
                updates_agents.append(stump_update)          # Transforma em toco
                new_entities_to_create.extend(dropped_logs)  # Agenda a criação dos 3 troncos no Neo4j
                
                # Remove a árvore da visão neste exato segundo para ele não bater nela de novo
                world_entities = [e for e in world_entities if e['id'] != target_id]

        elif action == "COLLECT_LOG":
            target_entity = next((e for e in world_entities if e['id'] == target_id), None)
            if target_entity:
                # === A TRAVA FÍSICA AQUI ===
                if survival_brain.inventory_sys.can_collect_log(inv):
                    inv['logs'] = inv.get('logs', 0) + 1
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"🪵 {agent_name} recolheu 1 Tronco para a mochila.", "timestamp": current_time})
                    dead_agents.append(target_id) 
                    world_entities = [e for e in world_entities if e['id'] != target_id]
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🎒 {agent_name} tentou recolher, mas a mochila de madeira está cheia (Limite: 10)!", "timestamp": current_time})

                      
        elif action == "COLLECT_STONE":
            target_entity = next((e for e in world_entities if e['id'] == target_id), None)
            if target_entity and survival_brain.inventory_sys.can_collect_stone(inv):
                inv['stones'] = inv.get('stones', 0) + 1
                events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"🪨 {agent_name} recolheu 1 Pedra.", "timestamp": current_time})
                dead_agents.append(target_id)
                world_entities = [e for e in world_entities if e['id'] != target_id]

        # === NOVA AÇÃO: Compra de Troncos (B2B) ===
        elif action == "TRADE_LOGS":
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent:
                seller_inv = survival_brain.inventory_sys.parse(target_agent.get('inventoryJSON', "{}"))
                
                buyer_data = {
                    "inventoryJSON": inv,
                    "hunger": agent.get('hunger', 100),
                    "lieLevel": agent.get('lieLevel', 0)
                }
                seller_data = {
                    "inventoryJSON": seller_inv,
                    "hunger": target_agent.get('hunger', 100),
                    "lieLevel": target_agent.get('lieLevel', 0)
                }
                
                deal = economy.negotiate_deal(buyer_data, seller_data, "logs", 1)
                
                if deal["success"]:
                    success, b_inv, s_inv, msg = economy.execute_trade(inv, seller_inv, "logs", deal["price"], 1)
                    if success:
                        inv = b_inv
                        target_agent['inventoryJSON'] = survival_brain.inventory_sys.to_string(s_inv)
                        for up in updates_agents:
                            if up['id'] == target_id:
                                up['inv'] = target_agent['inventoryJSON']
                        
                        events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🤝 {agent_name} comprou 1 Tronco de {target_agent.get('name', 'Lenhador')} por {deal['price']} Plobs. (Aceitaria até {deal['buyer_ceiling']:.2f})", "timestamp": current_time})
                    else:
                        events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ {agent_name} fechou negócio a {deal['price']}, mas a troca falhou: {msg}.", "timestamp": current_time})
                        # O comprador regista o boicote na memória RAM!
                        survival_brain.memory_sys._ensure_agent(agent['id'])
                        survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"💸 Falha de Mercado B2B: {agent_name} ofereceu {deal['buyer_ceiling']:.2f} Plobs, mas o vendedor exigiu {deal['seller_floor']:.2f}!", "timestamp": current_time})
                    
                    # === NOVO: O Item ficou escasso/inflacionado! ===
                    EconomySystem.register_scarcity("logs") # (Use "potatoes" na ação de TRADE normal)
                    
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick

        elif action == "CRAFT_FENCE":
            # Agora custa 2 TRONCOS (Logs)
            if inv.get('logs', 0) >= 2 and survival_brain.inventory_sys.can_carry_fence(inv):
                inv['logs'] -= 2
                inv['fences'] = inv.get('fences', 0) + 1
                biology.process_tick(agent, "ACTION") # Gasta energia
                events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"⚒️ {agent_name} fabricou uma cerca (Consumiu 2 Madeiras).", "timestamp": current_time})

        elif action == "REPAIR_FENCE":
            target_entity = next((e for e in world_entities if e['id'] == target_id), None)
            # Encontra o cliente (o fazendeiro mais próximo da cerca)
            customer = min([a for a in agents if a['type'] == 'farmer'], 
                           key=lambda f: math.hypot(f['posX']-target_entity['x'], f['posZ']-target_entity['z']), 
                           default=None)
            
            if target_entity and inv.get('fences', 0) > 0 and customer:
                cust_inv = survival_brain.inventory_sys.parse(customer.get('inventoryJSON', "{}"))
                fee = economy.BASE_PRICES['fences'] * 0.8
                
                # O dinheiro sai do Fazendeiro para o Construtor!
                if cust_inv.get('plobs', 0) >= fee:
                    cust_inv['plobs'] -= fee
                    inv['plobs'] += fee
                    inv['fences'] -= 1
                    customer['inventoryJSON'] = survival_brain.inventory_sys.to_string(cust_inv)
                    
                    # === A CORREÇÃO DE OURO AQUI ===
                    for up in updates_agents:
                        if up['id'] == customer['id']:
                            up['inv'] = customer['inventoryJSON']
                    
                    events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🚧 {agent_name} reparou a cerca. {customer['name']} pagou {fee} Plobs.", "timestamp": current_time})
                    
                    # CORREÇÃO: Restaura o HP para 100 e preserva a idade
                    updates_agents.append({"id": target_id, "type": "fence", "x": target_entity['x'], "z": target_entity['z'], "hp": 100.0, "hunger": 0, "age": target_entity.get('age', 0), "inv": "{}", "mem": "{}", "state": "IDLE"})
                    
        elif action == "TRADE":
            # Acha o parceiro de negócios na lista global
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent:
                buyer_inv_dict = inv 
                seller_inv_dict = survival_brain.inventory_sys.parse(target_agent.get('inventoryJSON', "{}"))
                
                buyer_data = {
                    "inventoryJSON": buyer_inv_dict,
                    "hunger": agent.get('hunger', 100),
                    "lieLevel": agent.get('lieLevel', 0)
                }
                seller_data = {
                    "inventoryJSON": seller_inv_dict,
                    "hunger": target_agent.get('hunger', 100),
                    "lieLevel": target_agent.get('lieLevel', 0)
                }

                deal = economy.negotiate_deal(buyer_data, seller_data, "potatoes", 1)
                
                if deal["success"]:
                    success, new_b_inv, new_s_inv, msg = economy.execute_trade(
                        buyer_inv_dict, seller_inv_dict, "potatoes", deal["price"], 1
                    )
                    
                    if success:
                        inv = new_b_inv 
                        target_agent['inventoryJSON'] = survival_brain.inventory_sys.to_string(new_s_inv)
                        
                        # === A CORREÇÃO DE OURO AQUI ===
                        for up in updates_agents:
                            if up['id'] == target_id:
                                up['inv'] = target_agent['inventoryJSON']
                        
                        events.append({
                            "id": str(uuid.uuid4()), 
                            "level": "SUCCESS", 
                            "message": f"🤝 {agent_name} comprou 1 Batata de {target_agent.get('name', 'Fazendeiro')} por {deal['price']:.2f} Plobs. (Aceitaria até {deal['buyer_ceiling']:.2f})", 
                            "timestamp": current_time
                        })
                    else:
                        events.append({
                            "id": str(uuid.uuid4()), 
                            "level": "WARNING", 
                            "message": f"❌ {agent_name} fechou negócio a {deal['price']:.2f}, mas a troca falhou: {msg}.", 
                            "timestamp": current_time
                        })
                        # O comprador regista o boicote na memória RAM!
                        survival_brain.memory_sys._ensure_agent(agent['id'])
                        survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick
                else:
                    events.append({
                        "id": str(uuid.uuid4()), 
                        "level": "WARNING", 
                        "message": f"💸 Falha de Mercado: {agent_name} ofereceu {deal['buyer_ceiling']:.2f} Plobs, mas {target_agent.get('name', 'Fazendeiro')} exigiu no mínimo {deal['seller_floor']:.2f} Plobs!", 
                        "timestamp": current_time
                    })
                    # O comprador regista o boicote na memória RAM!
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick

       # Adiciona a memória e estado ao pacote de atualização (PARA OS VIVOS)
        updates_agents.append({
            "id": agent['id'],
            "type": agent['type'], # <-- Mantém a profissão original intacta!
            "x": new_x, "z": new_z, 
            "hp": new_hp, "hunger": new_hunger,
            "age": agent.get('age', 0), # <--- GRAVAR A IDADE AQUI PARA OS VIVOS
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
        
    # === CRIAÇÃO DE NOVAS ENTIDADES (ex: Troncos caídos) ===
    if new_entities_to_create:
        session.run("""
        UNWIND $entities AS ent
        CREATE (e:Entity {
            id: ent.id, type: ent.type, posX: ent.posX, posY: ent.posY, posZ: ent.posZ,
            health: ent.health, hunger: ent.hunger, name: ent.name,
            inventoryJSON: ent.inventoryJSON, memoryJSON: ent.memoryJSON, state: ent.state
        })
        """, entities=new_entities_to_create)
        
    if updates_agents:
        session.run("""
        UNWIND $updates AS up
        MATCH (e:Entity {id: up.id})
        // O PULO DO GATO: Atualizamos o TIPO da entidade dinamicamente!
        // Se ele morreu, vira 'loot'. Se está vivo, continua 'farmer/builder/etc'
        SET e.type = up.type, 
            e.posX = up.x, 
            e.posZ = up.z, 
            e.health = up.hp, 
            e.hunger = up.hunger, 
            e.age = up.age,        // <--- A NOVA IDADE A SER SALVA NO BANCO!
            e.inventoryJSON = up.inv, 
            e.memoryJSON = up.mem, 
            e.state = up.state
        """, updates=updates_agents)
        
    if updates_tiles:
        session.run("""
        UNWIND $updates AS up
        MERGE (t:Tile {id: up.id})
        SET t.gridX = up.x, 
            t.gridZ = up.z, 
            t.type = up.type, 
            t.cropsJSON = coalesce(up.cropsJSON, '[]')
        """, updates=updates_tiles)
        
    # =====================================================================
    # === FASE 2: O LUTO BIOLÓGICO E A VIUVEZ (SOCIOLOGIA) ===
    # =====================================================================
    # Filtra os IDs de quem acabou de morrer neste exato tick
    dead_ids = [up['id'] for up in updates_agents if up.get('hp', 100) <= 0]
    
    if dead_ids:
        # A mágica do Grafo: Transforma o casamento ativo num luto histórico
        widows_query = """
        UNWIND $dead_ids AS dead_id
        MATCH (dead:Entity {id: dead_id})-[r:MARRIED_TO]-(widow:Entity)
        
        // 1. Cria o laço histórico para a Árvore Genealógica não esquecer
        CREATE (widow)-[:WIDOWED_FROM]->(dead)
        
        // 2. Destrói o casamento ativo e atualiza o estado civil
        DELETE r
        SET widow.married = false
        
        RETURN widow.name AS widow_name, dead.name AS dead_name
        """
        widow_results = session.run(widows_query, dead_ids=dead_ids)
        
        # 3. Dispara o evento de luto para o Terminal de Auditoria Biológica
        for record in widow_results:
            events.append({
                "id": str(uuid.uuid4()), 
                "level": "ERROR", 
                "message": f"🖤 LUTO: {record['widow_name']} chora a perda do seu parceiro(a), {record['dead_name']}. O estado civil voltou para solteiro.", 
                "timestamp": current_tick # Usando o tick atual como referência de tempo
            })
    # =====================================================================

    return {
        "message": "Tick Biológico processado",
        "events": events,
        "heatmap": [], 
        "lastAction": 0,
        "qValues": [0]*8, 
        "currentState": [0,0,0],
        "analytics": None
    }