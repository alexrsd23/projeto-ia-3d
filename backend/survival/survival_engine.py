import json
import random
import uuid
import math
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
    AGENT_TYPES = ['farmer', 'woodcutter', 'builder', 'blacksmith', 'wolf']

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
        coalesce(e.toolHp, 100.0) AS toolHp,
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
    # NOVO: Biologia do Mundo e Depreciação (Entropia Estrutural e Loot)
    # =====================================================================
    for entity in world_entities:
        if entity['type'] == 'fence':
            # 0.5% de chance da cerca quebrar a cada tick
            if random.random() < 0.0002:
                updates_agents.append({
                    "id": entity['id'], "type": "damaged_fence", 
                    "x": entity['x'], "z": entity['z'],
                    "hp": 0, "hunger": 0, "inv": "{}", "mem": "{}", "state": "IDLE"
                })
                
        # === CORREÇÃO ESTOCÁSTICA: DECOMPOSIÇÃO DE ESPÓLIOS ===
        # Um saco de loot abandonado decai lentamente (equivale a ~10 minutos reais)
        elif entity['type'] == 'loot':
            if random.random() < 0.0005: 
                dead_agents.append(entity['id'])
                events.append({
                    "id": str(uuid.uuid4()), "level": "INFO", 
                    "message": f"🍂 ECOLOGIA: Um espólio antigo decompôs-se e regressou à terra em X:{entity['x']}, Z:{entity['z']}.", 
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
    # =====================================================================
    # NOVO: CICLO GEOLÓGICO (Geração Espontânea e Distribuída de Rochas)
    # =====================================================================
    # === CORREÇÃO ESTOCÁSTICA: TETO DE DENSIDADE MINERAL ===
    # O mapa 48x48 tem ~625 nós. Limitamos o volume global de pedras ativas a 60 unidades.
    current_stone_count = sum(1 for e in world_entities if e.get('type') == 'stone')
    
    if current_stone_count < 60 and random.random() < 0.10:
        rx = random.choice(range(-24, 25, 2))
        rz = random.choice(range(-24, 25, 2))
        
        is_valid_spot = True
        
        # 1. Restrição de Propriedade e Buffer (1 Bloco de Isolamento = 2 Unidades)
        for p in world_plots:
            # Amplia a caixa delimitadora (Bounding Box) do terreno
            px_min = p['startX'] - 2
            pz_min = p['startZ'] - 2
            px_max = p['startX'] + (p['width'] - 1) * 2 + 2
            pz_max = p['startZ'] + (p['height'] - 1) * 2 + 2
            
            if px_min <= rx <= px_max and pz_min <= rz <= pz_max:
                is_valid_spot = False
                break
                
        if is_valid_spot:
            # 2 e 3. Restrição de Solo Ocupado e Controle de Densidade
            for e in world_entities:
                ex, ez = e.get('x'), e.get('z')
                if ex is None or ez is None: continue
                
                # Regra Absoluta: Nenhum objeto sobrepondo a nova pedra
                if ex == rx and ez == rz:
                    is_valid_spot = False
                    break
                    
                # Regra de Densidade: Proíbe pedras adjacentes (raio restrito de 3.0)
                if e.get('type') == 'stone':
                    if math.hypot(ex - rx, ez - rz) <= 3.0:
                        is_valid_spot = False
                        break
                        
        if is_valid_spot:
            current_time_geo = datetime.now().strftime("%H:%M:%S")
            new_stone = {
                "id": str(uuid.uuid4()), "type": "stone", "posX": rx, "posY": -0.5, "posZ": rz,
                "health": 100.0, "hunger": 0.0, "name": "Pedra", "inventoryJSON": "{}", "memoryJSON": "{}", "state": "IDLE"
            }
            new_entities_to_create.append(new_stone)
            # Injeta imediatamente no array volátil para que a leitura de colisões deste mesmo tick já a considere
            world_entities.append({"id": new_stone['id'], "type": "stone", "x": rx, "z": rz, "hp": 100.0})
            events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"⛰️ GEOLOGIA: Um novo afloramento rochoso irrompeu do solo em X:{rx}, Z:{rz}.", "timestamp": current_time_geo})
    # =====================================================================

    for agent in agents:
        inv = survival_brain.inventory_sys.parse(agent.get('inventoryJSON', "{}"))
        tool_hp = agent.get('toolHp', 100.0)
        
        # === NOVA MECÂNICA: ENTROPIA BIOLÓGICA (APODRECIMENTO) ===
        # A cada tick, há 0.1% de chance de UMA batata apodrecer no inventário (se existir).
        # Isso força os fazendeiros a venderem o excedente rápido ou plantarem,
        # impedindo a inflação estagnada de "bilionários da batata".
        if inv.get('potatoes', 0) > 0 and random.random() < 0.001:
            inv['potatoes'] -= 1
            agent_name_for_rot = agent.get('name', f"Agente {agent['id'][:4]}")
            current_time_for_rot = datetime.now().strftime("%H:%M:%S")
            events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🪰 ENTROPIA: Uma batata apodreceu na mochila de {agent_name_for_rot}!", "timestamp": current_time_for_rot})
            
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
        raw_mem_updated = survival_brain.memory_sys.agent_memories.get(agent['id'], {})
        safe_memory = {
            "food": {f"{k[0]},{k[1]}": v for k, v in raw_mem_updated.get('food', {}).items()},
            "farms": {f"{k[0]},{k[1]}": v for k, v in raw_mem_updated.get('farms', {}).items()},
            "hazards": {f"{k[0]},{k[1]}": v for k, v in raw_mem_updated.get('hazards', {}).items()},
            "rejections": raw_mem_updated.get('rejections', []),
            "active_contract": raw_mem_updated.get('active_contract'),
            "ignored_loots": raw_mem_updated.get('ignored_loots', {}) # <--- NOVO: Salva os sacos ignorados
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
            
            # =================================================================
            # === NOVO: SUCESSÃO PATRIMONIAL E AVALIAÇÃO DE HERDEIROS ===
            # =================================================================
            # A query agora verifica APENAS familiares vivos (health > 0 e type não é loot).
            query_heirs = """
            MATCH (dead:Entity {id: $id})-[:OWNS]->(p:Plot)
            OPTIONAL MATCH (dead)-[:MARRIED_TO]-(spouse:Entity)
              WHERE coalesce(spouse.health, 0) > 0 AND spouse.type <> 'loot'
            OPTIONAL MATCH (dead)-[:PARENT_OF]->(child:Entity)
              WHERE coalesce(child.health, 0) > 0 AND child.type <> 'loot'
            WITH dead, collect(DISTINCT p.id) AS owned_plots, 
                 collect(DISTINCT spouse.id) AS spouses, 
                 collect(DISTINCT child.id) AS children
            RETURN owned_plots, spouses, children
            """
            heir_results = session.run(query_heirs, id=agent['id']).data()
            
            if heir_results and heir_results[0]['owned_plots']:
                record = heir_results[0]
                plots = record['owned_plots']
                spouses = record['spouses']
                children = record['children']
                
                if spouses:
                    # REGRA 1 (Cônjuge Meeiro): O parceiro sobrevivo herda todas as terras
                    heir_id = spouses[0] 
                    session.run("""
                    UNWIND $plots AS plotId
                    MATCH (p:Plot {id: plotId})
                    MATCH (heir:Entity {id: $heirId})
                    MATCH (dead:Entity {id: $deadId})-[r:OWNS]->(p)
                    DELETE r
                    MERGE (heir)-[:OWNS]->(p)
                    """, plots=plots, heirId=heir_id, deadId=agent['id'])
                    
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"📜 SUCESSÃO: O parceiro de {agent_name} herdou as suas {len(plots)} propriedades.", "timestamp": current_time})
                    
                    for wp in world_plots:
                        if wp['id'] in plots:
                            wp['ownerId'] = heir_id
                            
                elif children:
                    # REGRA 2 (Partilha de Bens): Ausência de cônjuge. Divide os terrenos equitativamente pelos filhos.
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"📜 PARTILHA: As {len(plots)} propriedades de {agent_name} foram divididas entre os seus {len(children)} descendentes vivos.", "timestamp": current_time})
                    
                    for idx, plot_id in enumerate(plots):
                        # Algoritmo Round-Robin para garantir que nenhum filho é favorecido em excesso
                        heir_id = children[idx % len(children)]
                        session.run("""
                        MATCH (p:Plot {id: $plotId})
                        MATCH (heir:Entity {id: $heirId})
                        MATCH (dead:Entity {id: $deadId})-[r:OWNS]->(p)
                        DELETE r
                        MERGE (heir)-[:OWNS]->(p)
                        """, plotId=plot_id, heirId=heir_id, deadId=agent['id'])
                        
                        for wp in world_plots:
                            if wp['id'] == plot_id:
                                wp['ownerId'] = heir_id
                                
                else:
                    # REGRA 3 (Usucapião): Sem família viva. O latifúndio torna-se propriedade do Estado/Devoluta.
                    session.run("""
                    UNWIND $plots AS plotId
                    MATCH (dead:Entity {id: $deadId})-[r:OWNS]->(p:Plot {id: plotId})
                    DELETE r
                    SET p.status = 'abandoned'
                    """, plots=plots, deadId=agent['id'])
                    
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🏚️ TERRA DEVOLUTA: {agent_name} não deixou herdeiros. {len(plots)} parcelas estão livres para USUCAPIÃO!", "timestamp": current_time})
                    
                    for wp in world_plots:
                        if wp['id'] in plots:
                            wp['ownerId'] = None
                            wp['status'] = 'abandoned'
            # =================================================================
            
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
        
       # 3. Execução das Ações Físicas (Logs de Sucesso/Morte)
        
        # === NOVO: AVALIAÇÃO DE CONCORRÊNCIA ===
        # Adicionadas as chaves que faltavam para evitar bloqueios fantasmas
        if action not in ["IDLE", "MOVE", "EAT_INVENTORY", "CRAFT_FENCE", "CRAFT_GATE", "PROPOSE_MARRIAGE", "RESERVE_PLOT", "FINISH_CONTRACT", "HIRE_BUILDER", "BUILD_NEW_FENCE", "BUILD_NEW_GATE", "TRADE_LOGS_BULK", "CRAFT_TREE_SEED", "TRADE_TREE_SEED", "PLANT_TREE", "CRAFT_METAL_PART", "FORAGE_SEED", "REQUEST_REPAIR", "TRADE", "CLAIM_PLOT"]:
            
            # === CORREÇÃO CRÍTICA: EXTRAÇÃO POLIMÓRFICA SEGURA ===
            # Garante que dicionários com chaves alternativas (stump_id, tile_id, plot_id) 
            # sejam bloqueados corretamente na malha de concorrência sem quebrar o motor.
            if isinstance(target_id, dict):
                t_id = target_id.get("id") or target_id.get("stump_id") or target_id.get("tile_id") or target_id.get("plot_id")
            else:
                t_id = target_id

            if t_id:
                if t_id in locked_targets:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"⏳ {agent_name} hesitou! Outro agente interagiu com o alvo primeiro.", "timestamp": current_time})
                    # === CORREÇÃO: Em vez de abortar o tick e gerar amnésia, anula-se fisicamente a ação
                    action = "IDLE" 
                else:
                    locked_targets.add(t_id) # Tranca o alvo para o resto deste tick!
                    
        # === A CORREÇÃO ESTRUTURAL (DE ELIF PARA IF) ===
        # Ao usar 'if', quebramos a cadeia. Agora as ações serão executadas!
        if action == "TRADE_LOGS_BULK":
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent:
                seller_inv = survival_brain.inventory_sys.parse(target_agent.get('inventoryJSON', "{}"))
                buyer_data = { "inventoryJSON": inv, "hunger": agent.get('hunger', 100), "lieLevel": agent.get('lieLevel', 0) }
                seller_data = { "inventoryJSON": seller_inv, "hunger": target_agent.get('hunger', 100), "lieLevel": target_agent.get('lieLevel', 0) }
                
                # Altere a invocação para passar os nomes e extrair o chat
                deal = economy.negotiate_deal(buyer_data, seller_data, "logs", 1, agent_name, target_agent.get('name'))
                for msg in deal.get("chat_log", []):
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": msg, "timestamp": current_time})
                if deal["success"]:
                    unit_price = deal["price"]
                    seller_stock = seller_inv.get("logs", 0)
                    buyer_space = survival_brain.inventory_sys.MAX_LOGS - inv.get("logs", 0)
                    buyer_funds = inv.get("plobs", 0.0)
                    
                    # Reserva de emergência
                    current_potato_price = economy.evaluate_item_value("potatoes", inv, 100.0, agent.get('lieLevel', 0))
                    emergency_fund = current_potato_price * 3.0
                    disposable_funds = max(0.0, buyer_funds - emergency_fund)
                    
                    max_affordable = int(disposable_funds // unit_price) if unit_price > 0 else buyer_space
                    qty_to_buy = min(seller_stock, buyer_space, max_affordable)
                    
                    if qty_to_buy > 0:
                        success, b_inv, s_inv, msg = economy.execute_trade(inv, seller_inv, "logs", unit_price, qty_to_buy)
                        if success:
                            inv = b_inv
                            target_agent['inventoryJSON'] = survival_brain.inventory_sys.to_string(s_inv)
                            for up in updates_agents:
                                if up['id'] == target_id: up['inv'] = target_agent['inventoryJSON']
                            events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🤝 LOTE B2B: {agent_name} investiu {unit_price * qty_to_buy:.2f} Plobs em {qty_to_buy} Troncos.", "timestamp": current_time})
                        else:
                            events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ Liquidação em lote falhou: {msg}.", "timestamp": current_time})
                    else:
                        events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ Lote abortado: {agent_name} limitou a compra por falta de espaço, lenhador zerado ou para preservar seu Fundo de Emergência.", "timestamp": current_time})
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"💸 Falha de Mercado: {agent_name} achou a madeira muito cara.", "timestamp": current_time})
                    EconomySystem.register_scarcity("logs")
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick

        elif action == "CLAIM_PLOT":
            plot_id = target_id
            target_plot = next((p for p in world_plots if p['id'] == plot_id), None)
            
            if target_plot and target_plot.get('status') == 'abandoned':
                target_plot['ownerId'] = agent['id']
                target_plot['status'] = 'planned' # Devolve a terra à economia ativa
                
                try:
                    # Efetiva a posse legal no Grafo
                    session.run("""
                    MATCH (p:Plot {id: $plotId})
                    MATCH (new_owner:Entity {id: $ownerId})
                    SET p.status = 'planned'
                    MERGE (new_owner)-[:OWNS]->(p)
                    """, plotId=plot_id, ownerId=agent['id'])
                    
                    events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"📜 USUCAPIÃO DEFERIDO: {agent_name} assumiu a posse definitiva do terreno abandonado!", "timestamp": current_time})
                except Exception as e:
                    events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"Erro jurídico no usucapião: {str(e)}", "timestamp": current_time})
            else:
                events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"⚖️ {agent_name} chegou tarde. O terreno já foi legalmente apropriado por outro agente.", "timestamp": current_time})
        
        elif action == "CRAFT_METAL_PART":
            if inv.get('stones', 0) >= 2:
                tool_hp = max(0.0, tool_hp - 1.0) # <--- CORREÇÃO: Adicionado o desgaste da ferramenta
                inv['stones'] -= 2
                inv['metal_parts'] = inv.get('metal_parts', 0) + 1
                biology.process_tick(agent, "ACTION")
                events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"⚒️ {agent_name} forjou 1 Peça Metálica no calor da bigorna.", "timestamp": current_time})
                
        elif action == "CRAFT_TREE_SEED":
            if inv.get('stones', 0) >= 1:
                tool_hp = max(0.0, tool_hp - 1.0) # Desgaste ligeiro
                inv['stones'] -= 1
                inv['tree_seed'] = inv.get('tree_seed', 0) + 2
                biology.process_tick(agent, "ACTION")
                events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"⚒️ {agent_name} moeu minerais e forjou 2 Kits de Reflorestamento.", "timestamp": current_time})

        elif action == "TRADE_TREE_SEED":
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent and target_agent['type'] == 'blacksmith':
                seller_inv = survival_brain.inventory_sys.parse(target_agent.get('inventoryJSON', "{}"))
                buyer_data = { "inventoryJSON": inv, "hunger": agent.get('hunger', 100), "lieLevel": agent.get('lieLevel', 0) }
                seller_data = { "inventoryJSON": seller_inv, "hunger": target_agent.get('hunger', 100), "lieLevel": target_agent.get('lieLevel', 0) }
                
                # Compra Múltipla Inteligente B2B
                deal = economy.negotiate_deal(buyer_data, seller_data, "tree_seed", 1, agent_name, target_agent.get('name'))
                for msg in deal.get("chat_log", []):
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": msg, "timestamp": current_time})
                if deal["success"]:
                    unit_price = deal["price"]
                    seller_stock = seller_inv.get("tree_seed", 0)
                    buyer_space = survival_brain.inventory_sys.MAX_TREE_SEEDS - inv.get("tree_seed", 0)
                    
                    # Trava Anti-Suicídio: O Lenhador não pode gastar o dinheiro da comida!
                    current_potato_price = economy.evaluate_item_value("potatoes", inv, 100.0, agent.get('lieLevel', 0))
                    emergency_fund = current_potato_price * 3.0
                    disposable_funds = max(0.0, inv.get("plobs", 0.0) - emergency_fund)
                    
                    max_affordable = int(disposable_funds // unit_price) if unit_price > 0 else buyer_space
                    qty_to_buy = min(seller_stock, buyer_space, max_affordable)
                    
                    if qty_to_buy > 0:
                        success, b_inv, s_inv, msg = economy.execute_trade(inv, seller_inv, "tree_seed", unit_price, qty_to_buy)
                        if success:
                            inv = b_inv
                            target_agent['inventoryJSON'] = survival_brain.inventory_sys.to_string(s_inv)
                            for up in updates_agents:
                                if up['id'] == target_id: up['inv'] = target_agent['inventoryJSON']
                            events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🤝 {agent_name} adquiriu {qty_to_buy} Kits de Plantio por {unit_price * qty_to_buy:.2f} Plobs.", "timestamp": current_time})
                        else:
                            events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ Compra abortada internamente: {msg}.", "timestamp": current_time})
                    else:
                        events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ {agent_name} abortou o negócio de sementes para proteger o seu fundo de emergência alimentar.", "timestamp": current_time})
                        survival_brain.memory_sys._ensure_agent(agent['id'])
                        survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"💸 Impasse Botânico: {agent_name} e {target_agent.get('name')} não concordaram com o preço do fertilizante.", "timestamp": current_time})
                    EconomySystem.register_scarcity("tree_seed")
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick

        # === NOVA FÍSICA APLICADA: PLANTIO E REPOSIÇÃO DE TOCOS ===
        elif action in ["PLANT_TREE", "REPLACE_STUMP"]:
            tx, tz = target_id["x"], target_id["z"]
            if inv.get('tree_seed', 0) > 0:
                tool_hp = max(0.0, tool_hp - 2.0) # Usar a pá cansa e desgasta
                inv['tree_seed'] -= 1
                
                # Se for reposição, precisamos arrancar o toco morto do ecossistema e do Neo4j
                if action == "REPLACE_STUMP":
                    stump_id = target_id.get("stump_id")
                    if stump_id:
                        dead_agents.append(stump_id)
                        world_entities = [e for e in world_entities if e['id'] != stump_id]

                # Correção Gravitacional: posY deve ser exatamente -0.5 para coincidir com a grade.
                new_tree = {
                    "id": str(uuid.uuid4()), "type": "tree", "posX": tx, "posY": -0.5, "posZ": tz,
                    "health": 100.0, "hunger": 0.0, "name": "Árvore", "inventoryJSON": "{}", "memoryJSON": "{}", "state": "IDLE"
                }
                new_entities_to_create.append(new_tree)
                
                # Injeção Imediata no Buffer Visual para evitar concorrência física no mesmo tick
                world_entities.append({"id": new_tree['id'], "type": "tree", "x": tx, "z": tz, "hp": 100.0})
                
                biology.process_tick(agent, "ACTION")
                msg_log = "🌲 ECOLOGIA: Extraiu o toco morto e plantou uma nova muda!" if action == "REPLACE_STUMP" else "🌲 CICLO VITAL: Semeou uma muda selvagem em solo livre."
                events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": msg_log, "timestamp": current_time})

        elif action == "CRAFT_GATE":
            # Atualizado para a nova receita!
            if inv.get('logs', 0) >= 2 and inv.get('stones', 0) >= 1 and inv.get('metal_parts', 0) >= 2:
                tool_hp = max(0.0, tool_hp - 2.0)
                inv['logs'] -= 2
                inv['stones'] -= 1
                inv['metal_parts'] -= 2
                inv['gates'] = inv.get('gates', 0) + 1
                biology.process_tick(agent, "ACTION")
                events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"⚒️ {agent_name} forjou o Portão Principal com reforços metálicos.", "timestamp": current_time})

        elif action == "TRADE_METAL_PARTS":
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent:
                seller_inv = survival_brain.inventory_sys.parse(target_agent.get('inventoryJSON', "{}"))
                buyer_data = { "inventoryJSON": inv, "hunger": agent.get('hunger', 100), "lieLevel": agent.get('lieLevel', 0) }
                seller_data = { "inventoryJSON": seller_inv, "hunger": target_agent.get('hunger', 100), "lieLevel": target_agent.get('lieLevel', 0) }
                
                deal = economy.negotiate_deal(buyer_data, seller_data, "metal_parts", 1, agent_name, target_agent.get('name'))
                for msg in deal.get("chat_log", []):
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": msg, "timestamp": current_time})
                if deal["success"]:
                    success, b_inv, s_inv, msg = economy.execute_trade(inv, seller_inv, "metal_parts", deal["price"], 1)
                    if success:
                        inv = b_inv
                        target_agent['inventoryJSON'] = survival_brain.inventory_sys.to_string(s_inv)
                        for up in updates_agents:
                            if up['id'] == target_id: up['inv'] = target_agent['inventoryJSON']
                        events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🤝 {agent_name} comprou 1 Peça Metálica de {target_agent.get('name')} por {deal['price']:.2f} Plobs.", "timestamp": current_time})
                    else:
                        events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ Troca de metais falhou: {msg}.", "timestamp": current_time})
                        # CORREÇÃO: Uso seguro da memória dinâmica e variável temporal local
                        survival_brain.memory_sys._ensure_agent(agent['id'])
                        survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"💸 Impasse Metalúrgico com {target_agent.get('name')}. O Construtor buscará outro fornecedor.", "timestamp": current_time})
                    EconomySystem.register_scarcity("metal_parts")
                    # CORREÇÃO: Uso seguro da memória dinâmica e variável temporal local
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick

        elif action == "BUILD_NEW_GATE":
            tx, tz = target_id["x"], target_id["z"]
            owner_id = target_id.get("plot_id", "").replace("plot-", "")
            customer = next((a for a in agents if a['id'] == owner_id), None)
            
            fee = economy.BASE_PRICES['gates']
            if customer and inv.get('gates', 0) > 0:
                tool_hp = max(0.0, tool_hp - 2.0)
                cust_inv = survival_brain.inventory_sys.parse(customer.get('inventoryJSON', "{}"))
                if cust_inv.get('plobs', 0) >= fee:
                    cust_inv['plobs'] -= fee
                    inv['plobs'] += fee
                    inv['gates'] -= 1
                    
                    customer['inventoryJSON'] = survival_brain.inventory_sys.to_string(cust_inv)
                    for up in updates_agents:
                        if up['id'] == customer['id']: up['inv'] = customer['inventoryJSON']
                            
                    new_gate = {
                        "id": str(uuid.uuid4()), "type": "gate", "posX": tx, "posY": -0.5, "posZ": tz,
                        "health": 100.0, "hunger": 0.0, "name": "Portão", "inventoryJSON": "{}", "memoryJSON": "{}", "state": "IDLE"
                    }
                    new_entities_to_create.append(new_gate)
                    world_entities.append({"id": new_gate['id'], "type": "gate", "x": tx, "z": tz, "hp": 100.0})
                    
                    events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🚪 {agent_name} instalou o portão para {customer.get('name')} por {fee} Plobs.", "timestamp": current_time})
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"❌ Obra Embargada: {customer.get('name')} faliu no meio da obra do portão!", "timestamp": current_time})
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    if 'active_contract' in survival_brain.memory_sys.agent_memories[agent['id']]:
                        del survival_brain.memory_sys.agent_memories[agent['id']]['active_contract']
        
        if action == "EAT_INVENTORY":
            if survival_brain.inventory_sys.consume_potato(inv):
                recovered = biology.consume_food({'hunger': new_hunger, 'hp': new_hp})
                new_hunger, new_hp = recovered['hunger'], recovered['hp']
                events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"{agent_name} — Inventário: Consumiu 1 batata (Nova fome: {new_hunger:.1f}%)", "timestamp": current_time})
        
        # === NOVA AÇÃO FÍSICA: EXTRAÇÃO DE SEMENTES ===
        elif action == "CRAFT_SEED":
            if survival_brain.inventory_sys.craft_seeds(inv):
                biology.process_tick(agent, "ACTION") # Trabalhar cansa!
                events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🌱 {agent_name} cortou 1 Batata e obteve 2 Sementes!", "timestamp": current_time})
            else:
                events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ Falha ao extrair sementes: Mochila de sementes cheia ou sem batatas.", "timestamp": current_time})
                
        elif action == "REQUEST_REPAIR":
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent and target_agent['type'] == 'blacksmith':
                smith_inv = survival_brain.inventory_sys.parse(target_agent.get('inventoryJSON', "{}"))
                buyer_data = { "inventoryJSON": inv, "hunger": agent.get('hunger', 100), "lieLevel": agent.get('lieLevel', 0) }
                seller_data = { "inventoryJSON": smith_inv, "hunger": target_agent.get('hunger', 100), "lieLevel": target_agent.get('lieLevel', 0) }

                deal = economy.negotiate_deal(buyer_data, seller_data, "tool_repair", 1, agent_name, target_agent.get('name'))
                for msg in deal.get("chat_log", []):
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": msg, "timestamp": current_time})
                
                # O Ferreiro precisa de pelo menos 1 Peça Metálica para consertar a ferramenta
                if deal["success"] and smith_inv.get('metal_parts', 0) >= 1:
                    if inv.get('plobs', 0) >= deal["price"]:
                        inv['plobs'] -= deal["price"]
                        smith_inv['plobs'] += deal["price"]
                        smith_inv['metal_parts'] -= 1
                        tool_hp = 100.0 # <--- FERRAMENTA RESTAURADA!
                        
                        target_agent['inventoryJSON'] = survival_brain.inventory_sys.to_string(smith_inv)
                        for up in updates_agents:
                            if up['id'] == target_id: up['inv'] = target_agent['inventoryJSON']
                            
                        tool_name = "a Enxada" if agent['type'] == 'farmer' else ("o Machado" if agent['type'] == 'woodcutter' else "o Martelo")
                        events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"⚒️ {agent_name} pagou {deal['price']:.2f} Plobs para {target_agent.get('name')} consertar {tool_name}!", "timestamp": current_time})
                    else:
                        events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"💸 {agent_name} não tem fundos para consertar a ferramenta.", "timestamp": current_time})
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"❌ O Ferreiro {target_agent.get('name')} não possui Peças Metálicas para o conserto ou recusou o valor.", "timestamp": current_time})
                    EconomySystem.register_scarcity("tool_repair")
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick
        
        elif action == "HIRE_BUILDER":
            target_agent = next((a for a in agents if a['id'] == target_id), None)
            if target_agent:
                # Verifica a RAM do construtor alvo
                t_mem = survival_brain.memory_sys.agent_memories.get(target_id, {})
                if not t_mem.get('active_contract'):
                    plot_id = f"plot-{agent['id']}"
                    survival_brain.memory_sys._ensure_agent(target_id)
                    survival_brain.memory_sys.agent_memories[target_id]['active_contract'] = {"plot_id": plot_id, "owner_id": agent['id']}
                    
                    events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"📝 CONTRATO: {agent_name} contratou o Construtor {target_agent.get('name')} para erguer cercas!", "timestamp": current_time})
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"⏳ {agent_name} tentou contratar o Construtor {target_agent.get('name')}, mas ele já tem uma obra noutro terreno!", "timestamp": current_time})
                    
                    # === CORREÇÃO: O Fazendeiro regista a rejeição para não assediar o construtor em loop ===
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick

        elif action == "FINISH_CONTRACT":
            survival_brain.memory_sys._ensure_agent(agent['id'])
            if 'active_contract' in survival_brain.memory_sys.agent_memories[agent['id']]:
                del survival_brain.memory_sys.agent_memories[agent['id']]['active_contract']
            events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"✅ {agent_name} finalizou e entregou a obra do contrato!", "timestamp": current_time})

        elif action == "BUILD_NEW_FENCE":
            tx, tz = target_id["x"], target_id["z"]
            owner_id = target_id.get("plot_id", "").replace("plot-", "")
            customer = next((a for a in agents if a['id'] == owner_id), None)
            
            fee = economy.BASE_PRICES['fences'] # O Construtor cobra o preço tabelado por cada bloco
            
            if customer and inv.get('fences', 0) > 0:
                tool_hp = max(0.0, tool_hp - 2.0)
                cust_inv = survival_brain.inventory_sys.parse(customer.get('inventoryJSON', "{}"))
                if cust_inv.get('plobs', 0) >= fee:
                    # Pagamento B2B
                    cust_inv['plobs'] -= fee
                    inv['plobs'] += fee
                    inv['fences'] -= 1
                    
                    customer['inventoryJSON'] = survival_brain.inventory_sys.to_string(cust_inv)
                    for up in updates_agents:
                        if up['id'] == customer['id']:
                            up['inv'] = customer['inventoryJSON']
                            
                    # Criação Física da Cerca
                    new_fence = {
                        "id": str(uuid.uuid4()), "type": "fence", "posX": tx, "posY": -0.5, "posZ": tz,
                        "health": 100.0, "hunger": 0.0, "name": "Cerca", "inventoryJSON": "{}", "memoryJSON": "{}", "state": "IDLE"
                    }
                    new_entities_to_create.append(new_fence)
                    # Hack visual: injeta no mundo de imediato para não empilhar duas cercas no mesmo segundo
                    world_entities.append({"id": new_fence['id'], "type": "fence", "x": tx, "z": tz, "hp": 100.0})
                    
                    events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"🚧 {agent_name} ergueu uma cerca para {customer.get('name')} por {fee} Plobs.", "timestamp": current_time})
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"❌ Obra Embargada: {customer.get('name')} ficou sem Plobs para pagar! O contrato foi cancelado.", "timestamp": current_time})
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    if 'active_contract' in survival_brain.memory_sys.agent_memories[agent['id']]:
                        del survival_brain.memory_sys.agent_memories[agent['id']]['active_contract']
               
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
                
                # === CALIBRAÇÃO DE EQUILÍBRIO (RESILIÊNCIA ESTRUTURAL) ===
                # Reduz o dano para 16.5 por impacto, exigindo obrigatoriamente
                # um mínimo de 6 a 7 tentativas ativas para romper a estrutura.
                fence_new_hp = current_hp - 16.5 
                
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
            
            # Substituímos o 'continue' problemático por 'pass' para não pular o salvamento de memória!
            if agent.get('married', False):
                pass 
            else:
                try:
                    # 1. VALIDAÇÃO DE CONSANGUINIDADE (TABU GENÉTICO)
                    query_incest = """
                    MATCH (a:Entity {id: $idA}), (b:Entity {id: $idB})
                    OPTIONAL MATCH p1=(a)-[:PARENT_OF*1..]->(b)
                    OPTIONAL MATCH p2=(b)-[:PARENT_OF*1..]->(a)
                    OPTIONAL MATCH p3=(a)<-[:PARENT_OF]-()-[:PARENT_OF]->(b)
                    OPTIONAL MATCH p4=(a)<-[:PARENT_OF]-()-[:PARENT_OF]-()-[:PARENT_OF]->(b)
                    OPTIONAL MATCH p5=(b)<-[:PARENT_OF]-()-[:PARENT_OF]-()-[:PARENT_OF]->(a)
                    RETURN (p1 IS NOT NULL OR p2 IS NOT NULL OR p3 IS NOT NULL OR p4 IS NOT NULL OR p5 IS NOT NULL) AS is_incest
                    LIMIT 1
                    """
                    incest_check = session.run(query_incest, idA=agent_a, idB=agent_b).single()
                    
                    if incest_check and incest_check["is_incest"]:
                        events.append({"id": str(uuid.uuid4()), "level": "ERROR", "message": f"🧬 TABU GENÉTICO: A biologia impediu o flerte! {agent_name} e o alvo são parentes próximos.", "timestamp": current_time})
                        
                        # Grava na memória e cai graciosamente para o bloco de salvamento no fim do loop
                        survival_brain.memory_sys._ensure_agent(agent_a)
                        survival_brain.memory_sys._ensure_agent(agent_b)
                        survival_brain.memory_sys.agent_memories[agent_a]['rejections'].append(agent_b)
                        survival_brain.memory_sys.agent_memories[agent_b]['rejections'].append(agent_a)
                    else:
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
            
            partner = next((a for a in agents if a['id'] == agent_b_id), None)
            if partner:
                if new_hunger < 70.0:
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": f"⏳ {agent_name} cedeu a iniciativa romântica ao parceiro neste ciclo.", "timestamp": current_time})
                else:
                    p_inv = survival_brain.inventory_sys.parse(partner.get('inventoryJSON', "{}"))
                    a_type = agent['type']
                    
                    # === NOVO: CÁLCULO DE CUSTO EXPONENCIAL ASSIMÉTRICO ===
                    mem_a = survival_brain.memory_sys.agent_memories.get(agent_a_id, {})
                    mem_b = survival_brain.memory_sys.agent_memories.get(agent_b_id, {})
                    
                    kids_a = mem_a.get('children_count', 0)
                    kids_b = mem_b.get('children_count', 0)
                    
                    mult_a = 2 ** kids_a
                    mult_b = 2 ** kids_b
                    
                    cost_a, cost_b = 0, 0
                    item_type = ""
                    
                    if a_type == 'farmer':
                        cost_a, cost_b, item_type = 2 * mult_a, 2 * mult_b, 'potatoes'
                    elif a_type == 'woodcutter':
                        cost_a, cost_b, item_type = 5 * mult_a, 5 * mult_b, 'logs'
                    elif a_type == 'builder':
                        cost_a, cost_b, item_type = 4 * mult_a, 4 * mult_b, 'stones'
                    elif a_type == 'blacksmith':
                        cost_a, cost_b, item_type = 2 * mult_a, 2 * mult_b, 'metal_parts'
                        
                    both_can_afford = inv.get(item_type, 0) >= cost_a and p_inv.get(item_type, 0) >= cost_b
                    
                    if both_can_afford:
                        # Deduz os materiais respeitando o histórico reprodutivo de cada um
                        inv[item_type] -= cost_a
                        p_inv[item_type] -= cost_b
                        
                        # Incrementa a certidão biológica de cada parceiro na RAM
                        mem_a['children_count'] = kids_a + 1
                        mem_b['children_count'] = kids_b + 1
                        
                        # O CUSTO BIOLÓGICO: Ter um filho consome 25% da barra de fome de ambos!
                        new_hunger = max(0.0, new_hunger - 25.0)
                        partner['hunger'] = max(0.0, float(partner.get('hunger', 100)) - 25.0)
                        
                        partner['inventoryJSON'] = survival_brain.inventory_sys.to_string(p_inv)
                        for up in updates_agents:
                            if up['id'] == agent_b_id:
                                up['hunger'] = partner['hunger']
                                up['inv'] = partner['inventoryJSON']
                                
                        child_dna = biology.mix_dna(agent, partner)
                        child_id = str(uuid.uuid4())
                        child_name = f"{child_dna['profession']} {child_id[:2].upper()}"
                        
                        # === NOVO: TRANSFERÊNCIA DE RIQUEZA INTERGERACIONAL ===
                        # Cada pai doa 10% da sua conta bancária para o recém-nascido
                        father_donation = round(inv.get('plobs', 0.0) * 0.10, 2)
                        mother_donation = round(p_inv.get('plobs', 0.0) * 0.10, 2)
                        
                        inv['plobs'] = round(inv.get('plobs', 0.0) - father_donation, 2)
                        p_inv['plobs'] = round(p_inv.get('plobs', 0.0) - mother_donation, 2)
                        
                        # Inicia a criança com os fundos doados
                        child_inv_json = json.dumps({"plobs": father_donation + mother_donation})
                        
                        # === CORREÇÃO DE INTEGRIDADE GENEALÓGICA ===
                        # Em vez de tentar gravar no banco a meio do tick, colocamos a criança 
                        # na fila global. Injetamos o 'parent_a_id' e 'parent_b_id' para o Neo4j ler no fim.
                        new_child = {
                            "id": child_id, 
                            "type": agent['type'], 
                            "posX": new_x, "posY": 0.5, "posZ": new_z,
                            "health": 100.0, "hunger": 100.0, "name": child_name,
                            "color": child_dna['color'], "sex": child_dna['sex'], 
                            "profession": child_dna['profession'],
                            "trustLevel": child_dna['trustLevel'], "lieLevel": child_dna['lieLevel'],
                            "married": False, "age": 0,
                            "inventoryJSON": child_inv_json, "memoryJSON": "{}", "state": "IDLE",
                            "parent_a_id": agent_a_id, # <--- O VÍNCULO SANGUÍNEO GRAVADO AQUI
                            "parent_b_id": agent_b_id  # <--- O VÍNCULO SANGUÍNEO GRAVADO AQUI
                        }
                        
                        new_entities_to_create.append(new_child)
                        
                        # Injeção imediata no buffer visual para evitar colisões
                        world_entities.append({
                            "id": child_id, "type": agent['type'], 
                            "x": new_x, "z": new_z, "hp": 100.0, "age": 0
                        })
                        
                        events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"👶 MILAGRE DA VIDA: {agent_name} e {partner.get('name')} tiveram um filho! Bem-vindo(a) {child_name}!", "timestamp": current_time})
                    else:
                        events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🚫 Tentativa de gravidez falhou: {agent_name} ou parceiro não têm os recursos materiais exigidos!", "timestamp": current_time})
                        # === CORREÇÃO DE ESTADO CRÍTICO (ANTI-LOOP DE GRAVIDEZ) ===
                        # Agente regista o cônjuge falido na lista de boicotes e ignora-o durante 50 ticks
                        survival_brain.memory_sys._ensure_agent(agent_a_id)
                        survival_brain.memory_sys.agent_memories[agent_a_id].setdefault('boycotts', {})[agent_b_id] = current_tick

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
                tool_hp = max(0.0, tool_hp - 2.0)
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
                
                # === NOVO: TRANSFERÊNCIA DINÂMICA ===
                inv, new_loot_inv, is_empty, transferred = survival_brain.inventory_sys.transfer_loot(inv, loot_inv)
                
                if transferred:
                    events.append({"id": str(uuid.uuid4()), "level": "SUCCESS", "message": f"💰 {agent_name} vasculhou um espólio e pegou o que conseguia carregar!", "timestamp": current_time})
                    
                    if is_empty:
                        # O saco secou. Marca para apagar do banco.
                        dead_agents.append(target_id)
                        world_entities = [e for e in world_entities if e['id'] != target_id]
                    else:
                        # Ainda sobrou coisa (ex: pedras, e o fazendeiro não pôde carregar)
                        target_entity['inventoryJSON'] = survival_brain.inventory_sys.to_string(new_loot_inv)
                        # Atualiza o saco no banco de dados para os outros poderem pegar o resto
                        updates_agents.append({
                            "id": target_id, "type": "loot", "x": target_entity['x'], "z": target_entity['z'], 
                            "hp": 0, "hunger": 0, "age": target_entity.get('age', 0), 
                            "inv": target_entity['inventoryJSON'], "mem": "{}", "state": "IDLE"
                        })
                else:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🎒 {agent_name} revistou um espólio, mas já tem a mochila cheia ou não é compatível com os itens.", "timestamp": current_time})
                    
                    # === CORREÇÃO: O Agente memoriza que este saco é inútil para ele e ignora-o ===
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('ignored_loots', {})[target_id] = current_tick

        elif action == "CHOP_TREE":
            target_entity = next((e for e in world_entities if e['id'] == target_id), None)
            if target_entity:
                tool_hp = max(0.0, tool_hp - 2.0)
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
                
                deal = economy.negotiate_deal(buyer_data, seller_data, "logs", 1, agent_name, target_agent.get('name'))
                for msg in deal.get("chat_log", []):
                    events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": msg, "timestamp": current_time})
                
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
                tool_hp = max(0.0, tool_hp - 2.0)
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
                
                # === CORREÇÃO: PROTEÇÃO DE SUBSISTÊNCIA DO VENDEDOR (SEM AMNÉSIA) ===
                # Um Fazendeiro nunca vende batatas se tiver 3 ou menos (precisa delas para comer e plantar)
                if target_agent.get('type') == 'farmer' and seller_inv_dict.get('potatoes', 0) <= 3:
                    events.append({"id": str(uuid.uuid4()), "level": "WARNING", "message": f"🚫 {target_agent.get('name', 'Vendedor')} recusou a venda! Não possui excedente de batatas para exportação.", "timestamp": current_time})
                    # O comprador regista o boicote para não chatear este vendedor temporariamente
                    survival_brain.memory_sys._ensure_agent(agent['id'])
                    survival_brain.memory_sys.agent_memories[agent['id']].setdefault('boycotts', {})[target_id] = current_tick
                    # AQUI FOI RETIRADO O 'CONTINUE'. O código agora flui em segurança, assegurando o salvamento do boicote no DB.
                else:   
                    # O resto do código do TRADE continua igual a partir daqui...
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

                    deal = economy.negotiate_deal(buyer_data, seller_data, "potatoes", 1, agent_name, target_agent.get('name'))
                    for msg in deal.get("chat_log", []):
                        events.append({"id": str(uuid.uuid4()), "level": "INFO", "message": msg, "timestamp": current_time})
                    
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

       # === CORREÇÃO DEFINITIVA: FOTOGRAFIA PÓS-AÇÃO ===
        raw_mem_final = survival_brain.memory_sys.agent_memories.get(agent['id'], {})
        safe_memory_final = {
            "food": {f"{k[0]},{k[1]}": v for k, v in raw_mem_final.get('food', {}).items()},
            "farms": {f"{k[0]},{k[1]}": v for k, v in raw_mem_final.get('farms', {}).items()},
            "hazards": {f"{k[0]},{k[1]}": v for k, v in raw_mem_final.get('hazards', {}).items()},
            "rejections": raw_mem_final.get('rejections', []),
            "active_contract": raw_mem_final.get('active_contract'),
            "ignored_loots": raw_mem_final.get('ignored_loots', {}),
            "boycotts": raw_mem_final.get('boycotts', {}),
            "children_count": raw_mem_final.get('children_count', 0)  # <--- CORREÇÃO: Serialização do gene demográfico
        }

        # Adiciona a memória e estado ao pacote de atualização (PARA OS VIVOS)
        updates_agents.append({
            "id": agent['id'],
            "type": agent['type'], # <-- Mantém a profissão original intacta!
            "x": new_x, "z": new_z, 
            "hp": new_hp, "hunger": new_hunger,
            "age": agent.get('age', 0), # <--- GRAVAR A IDADE AQUI PARA OS VIVOS
            "toolHp": tool_hp,          # <--- CORREÇÃO CRÍTICA 1: EXPORTA A DURABILIDADE
            "inv": survival_brain.inventory_sys.to_string(inv),
            "mem": json.dumps(safe_memory_final), # <-- USA A FOTOGRAFIA NOVA
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
        
    # === CRIAÇÃO DE NOVAS ENTIDADES (Árvores, Pedras E CRIANÇAS) ===
    if new_entities_to_create:
        session.run("""
        UNWIND $entities AS ent
        CREATE (e:Entity {
            id: ent.id, type: ent.type, posX: ent.posX, posY: ent.posY, posZ: ent.posZ,
            health: coalesce(ent.health, 100.0), hunger: coalesce(ent.hunger, 0.0), name: ent.name,
            inventoryJSON: coalesce(ent.inventoryJSON, '{}'), memoryJSON: coalesce(ent.memoryJSON, '{}'), state: coalesce(ent.state, 'IDLE'),
            color: ent.color, sex: ent.sex, profession: ent.profession,
            trustLevel: ent.trustLevel, lieLevel: ent.lieLevel,
            married: coalesce(ent.married, false), age: coalesce(ent.age, 0)
        })
        WITH e, ent
        // === O VÍNCULO DE DESCENDÊNCIA NO NEO4J ===
        // Se a entidade tiver os IDs dos pais (porque é uma criança), a relação PARENT_OF é forjada.
        OPTIONAL MATCH (parentA:Entity {id: coalesce(ent.parent_a_id, 'null')})
        OPTIONAL MATCH (parentB:Entity {id: coalesce(ent.parent_b_id, 'null')})
        FOREACH (p IN CASE WHEN parentA IS NOT NULL THEN [parentA] ELSE [] END |
            MERGE (p)-[:PARENT_OF]->(e)
        )
        FOREACH (p IN CASE WHEN parentB IS NOT NULL THEN [parentB] ELSE [] END |
            MERGE (p)-[:PARENT_OF]->(e)
        )
        """, entities=new_entities_to_create)
        
    # === CORREÇÃO: SANITIZAÇÃO DE DICIONÁRIOS (ANTI-CRASH) ===
    # Garante que entidades não-sencientes (Loot, Cercas) não quebrem a query por falta da chave
    for up in updates_agents:
        if 'toolHp' not in up:
            up['toolHp'] = 100.0
        
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
            e.toolHp = up.toolHp,  // <--- CORREÇÃO CRÍTICA 2: PERSISTÊNCIA FÍSICA NO BANCO
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