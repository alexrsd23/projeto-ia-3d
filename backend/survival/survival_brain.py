import random
import math
import json
from survival.inventory import InventorySystem
from survival.perception import PerceptionSystem
from survival.memory_system import SpatialMemory
from survival.economy_system import EconomySystem
from survival.biology import BiologySystem
from survival.market_intelligence import MarketIntelligence
from survival.farm_planner import FarmPlanner

class SurvivalController:
    def __init__(self):
        self.market_intel = MarketIntelligence(EconomySystem(), BiologySystem())
        self.inventory_sys = InventorySystem()
        self.perception_sys = PerceptionSystem()
        self.memory_sys = SpatialMemory()
        self.agent_states = {} 
        self.farm_planner = FarmPlanner()

    def decide_next_move(self, agent, world_entities, world_tiles, world_plots, current_tick, all_agents):
        agent_id = agent['id']
        agent_type = agent.get('type', 'farmer') 
        agent_pos = (agent['x'], agent['z'], agent_id) 
        raw_hunger = agent.get('hunger')
        hunger = float(raw_hunger) if raw_hunger is not None else 100.0
        
        inv = self.inventory_sys.parse(agent.get('inventoryJSON', "{}"))
        
        radar_data = self.perception_sys.scan_environment(agent_pos, world_entities, world_tiles, all_agents)
        self.memory_sys.update_from_perception(agent_id, radar_data, current_tick)
        
        # === MAPEAMENTO DE COLISÕES REFINADO (ALTA PERFORMANCE) ===
        blocked_coords = set()
        solid_types = {'fence', 'gate', 'tree', 'stump', 'cactus', 'wall'}
        
        # Estruturas que se conectam visualmente (Cercas e Portões)
        connectable_types = {'fence', 'gate', 'damaged_fence'}
        connectable_coords = set()
        
        # === NOVO: BLOQUEIA ÁREAS RESERVADAS NO BANCO (EXCETO PARA O DONO) ===
        for plot in world_plots:
            # Se o agente atual é o dono deste terreno, NÃO o adiciona aos obstáculos!
            if plot.get('ownerId') == agent_id:
                continue 
                
            p_start_x = plot['startX']
            p_start_z = plot['startZ']
            p_width = plot['width']
            p_height = plot['height']
            
            # Calcula a área inteira da fazenda reservada e marca como "Proibida"
            p_max_x = p_start_x + (p_width - 1) * 2
            p_max_z = p_start_z + (p_height - 1) * 2
            
            for x in range(p_start_x, p_max_x + 1, 2):
                for z in range(p_start_z, p_max_z + 1, 2):
                    blocked_coords.add((x, z))
        
        for e in world_entities:
            if e.get('x') is None or e.get('z') is None:
                continue
                
            ex = round(float(e['x']))
            ez = round(float(e['z']))
            etype = e.get('type')
            
            # 1. Registra os pilares principais
            if etype in solid_types:
                if etype == 'gate' and agent_type != 'wolf':
                    pass # Humanos passam livremente pelo portão
                else:
                    blocked_coords.add((ex, ez))
            
            # 2. Registra os nós conectáveis para calcularmos as frestas
            if etype in connectable_types:
                connectable_coords.add((ex, ez))

        # === O SEGREDO: PREENCHIMENTO DAS JUNÇÕES ===
        # As cercas estão em posições pares (0, 2, 4), mas as vigas de madeira as conectam.
        # Precisamos bloquear o espaço intermediário (ex: 1, 3, 5) para "selar" as paredes físicas!
        for (ex, ez) in connectable_coords:
            for dx, dz in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                if (ex + dx, ez + dz) in connectable_coords:
                    junction_x = ex + dx // 2
                    junction_z = ez + dz // 2
                    blocked_coords.add((junction_x, junction_z))
                
        # =========================================================
        # 1. A MENTE DO PREDADOR (Comportamento Isolado do Lobo)
        # =========================================================
        if agent_type == 'wolf':
            # O instinto predatório ativa muito cedo (95%)
            is_aggressive = hunger < 95.0
            
            if is_aggressive:
                self.agent_states[agent_id] = "HUNTING"
                preys = [p for p in radar_data.get('other_agents', []) if p['type'] in ['farmer', 'woodcutter', 'builder']]
                
                if preys:
                    target_prey = preys[0] 
                    
                    # A) Mordida letal: Se estiver colado na presa
                    if target_prey['dist'] <= 3.0:
                        return ("ATTACK_AGENT", agent_pos[0], agent_pos[1], target_prey['id'], f"Atacando ferozmente {target_prey['name']}!")
                    
                    # === A CORREÇÃO DA INTELIGÊNCIA VEM AQUI ===
                    # B) Movimento: O lobo tenta SEMPRE andar em direção à presa primeiro
                    move_decision = self._move_towards(agent_pos, (target_prey['x'], target_prey['z']), blocked_coords, f"Farejou presa e está a perseguir!")
                    
                    # C) Obstáculo: Se a decisão de movimento o manteve no mesmo X e Z atual, significa que ele esbarrou numa parede física
                    is_stuck = move_decision[1] == agent_pos[0] and move_decision[2] == agent_pos[1]
                    
                    # D) Se bateu na parede, procura a cerca mais próxima para destruir e abrir caminho
                    if is_stuck and radar_data.get('fences'):
                        target_fence = radar_data['fences'][0]
                        if target_fence['dist'] <= 3.0:
                            return ("ATTACK_FENCE", agent_pos[0], agent_pos[1], target_fence['id'], f"Caminho bloqueado! Destruindo cerca para alcançar presa!")

                    # Se não estiver preso (por exemplo, se houver um buraco na cerca), ele apenas retorna o passo do movimento!
                    return move_decision
            
            self.agent_states[agent_id] = "PATROLLING"
            return self._wander(agent_pos, blocked_coords, "Saciado. Patrulhando território pacificamente.")

        # === ZONAS PSICOLÓGICAS ===
        is_critical = hunger < 25     
        is_hungry = hunger < 60       
        is_comfortable = hunger >= 60 
        needs_stock = self.inventory_sys.needs_replenish(inv)
        
        # === PRIORIDADE ABSOLUTA: INSTINTO DE FUGA (MEDO) ===
        if agent_type != 'wolf':
            wolves = [p for p in radar_data.get('other_agents', []) if p['type'] == 'wolf']
            if wolves:
                nearest_wolf = wolves[0] 
                if nearest_wolf['dist'] <= 5.0: 
                    self.agent_states[agent_id] = "FLEEING"
                    
                    dx = agent_pos[0] - nearest_wolf['x']
                    dz = agent_pos[1] - nearest_wolf['z']
                    
                    move_x = 2 if dx > 0 else (-2 if dx < 0 else random.choice([-2, 2]))
                    move_z = 2 if dz > 0 else (-2 if dz < 0 else random.choice([-2, 2]))
                    
                    new_x = max(-24, min(24, agent_pos[0] + move_x))
                    new_z = max(-24, min(24, agent_pos[1] + move_z))
                    
                    # Usa a nova validação segura
                    if self._is_move_valid(agent_pos, new_x, new_z, move_x, move_z, blocked_coords):
                        return ("MOVE", new_x, new_z, None, f"Fugindo em pânico! Lobo detectado a {nearest_wolf['dist']:.1f} blocos!")
                    else:
                        return self._wander(agent_pos, blocked_coords, "Curralado! Tentando achar saída para fugir do predador!")
                    
       # === PRIORIDADE 2: INSTINTO SOCIAL E REPRODUTIVO ===
        if agent_type != 'wolf' and hunger >= 30.0:
            is_married = agent.get('married', False)
            
            if not is_married:
                my_rejections = self.memory_sys.agent_memories.get(agent_id, {}).get('rejections', [])
                
                potential_partners = [
                    p for p in radar_data.get('other_agents', []) 
                    if p['type'] == agent_type and p.get('married', False) == False and p['id'] not in my_rejections
                ]
                
                if potential_partners:
                    partner = potential_partners[0] 
                    if partner['dist'] <= 3.0:
                        self.agent_states[agent_id] = "PROPOSING"
                        return ("PROPOSE_MARRIAGE", agent_pos[0], agent_pos[1], partner['id'], f"Pedindo {partner['name']} em casamento!")
                    else:
                        self.agent_states[agent_id] = "COURTING"
                        return self._move_towards(agent_pos, (partner['x'], partner['z']), blocked_coords, f"Indo conhecer {partner['name']}.")
            else:
                can_afford_child = False
                if agent_type == 'farmer' and inv.get('potatoes', 0) >= 2:
                    can_afford_child = True
                elif agent_type == 'woodcutter' and inv.get('logs', 0) >= 5:
                    can_afford_child = True
                elif agent_type == 'builder' and inv.get('stones', 0) >= 5:
                    can_afford_child = True

                if hunger >= 70.0 and can_afford_child:
                    my_sex = agent.get('sex', 'M')
                    target_sex = 'F' if my_sex == 'M' else 'M'
                    
                    spouses = [
                        p for p in radar_data.get('other_agents', [])
                        if p['type'] == agent_type and p.get('married', False) == True and p.get('sex') == target_sex
                    ]
                    
                    if spouses:
                        spouse = spouses[0] 
                        if spouse['dist'] <= 3.0:
                            self.agent_states[agent_id] = "PROCREATING"
                            return ("PROCREATE", agent_pos[0], agent_pos[1], spouse['id'], f"Momento romântico com {spouse['name']}...")
                        else:
                            self.agent_states[agent_id] = "COURTING"
                            return self._move_towards(agent_pos, (spouse['x'], spouse['z']), blocked_coords, f"Indo encontrar {spouse['name']} para ter um filho.")
        
        # PRIORIDADE 0: Auto-Regulação Preventiva
        if is_hungry and self.inventory_sys.has_food(inv):
            self.agent_states[agent_id] = "SNACKING"
            log = f"Avaliando necessidades: Fome moderada ({hunger:.1f}%). Consumindo 1 batata preventiva."
            return ("EAT_INVENTORY", agent_pos[0], agent_pos[1], None, log)
            
        # PRIORIDADE 1: FOME REAL
        if is_critical or (is_hungry and not self.inventory_sys.has_food(inv)):
            self.agent_states[agent_id] = "SEEK_FOOD"
            if agent_type == 'farmer':
                if radar_data.get('food_ready'):
                    target = radar_data['food_ready'][0] 
                    if target['dist'] <= 3:
                        return ("HARVEST", agent_pos[0], agent_pos[1], target['tile_id'], "Colhendo batata madura.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo colher comida.")
            else:
                self.agent_states[agent_id] = "SEEK_TRADE"
                
                my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                active_boycotts = [f_id for f_id, tick_banned in my_boycotts.items() if current_tick - tick_banned < 50]
                
                farmers = [p for p in radar_data.get('other_agents', []) if p['type'] == 'farmer' and p['id'] not in active_boycotts]
                
                if farmers:
                    target_farmer = farmers[0]
                    if target_farmer['dist'] <= 3:
                        return ("TRADE", agent_pos[0], agent_pos[1], target_farmer['id'], f"Iniciando negociação de comida com {target_farmer['name']}.")
                    return self._move_towards(agent_pos, (target_farmer['x'], target_farmer['z']), blocked_coords, f"Perseguindo o fazendeiro {target_farmer['name']} para comprar comida.")
                else:
                    return self._wander(agent_pos, blocked_coords, "Comida está muito cara ou não há fazendeiros justos por perto. Explorando alternativas.")

        # PRIORIDADE 2: TRABALHO
        if is_comfortable:
            will_work = self.market_intel.should_work(agent.get('profession', ''), hunger, agent.get('lieLevel', 0))
            if not will_work:
                self.agent_states[agent_id] = "STRIKE"
                return self._wander(agent_pos, blocked_coords, "Greve: O preço da comida está tão alto que as calorias gastas dariam prejuízo.")

            if agent_type == 'woodcutter':
                if not self.inventory_sys.can_collect_log(inv):
                    self.agent_states[agent_id] = "FULL_INVENTORY"
                    return self._wander(agent_pos, blocked_coords, "Mochila de madeira cheia! Vagando até encontrar um comprador.")

                if radar_data.get('logs_on_ground'):
                    self.agent_states[agent_id] = "COLLECTING"
                    target = radar_data['logs_on_ground'][0]
                    if target['dist'] <= 3:
                        return ("COLLECT_LOG", agent_pos[0], agent_pos[1], target['id'], "Apanhando tronco do chão para a mochila.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo recolher um tronco caído.")

                self.agent_states[agent_id] = "CHOPPING"
                if radar_data.get('trees'):
                    target = radar_data['trees'][0]
                    if target['dist'] <= 3:
                        return ("CHOP_TREE", agent_pos[0], agent_pos[1], target['id'], "Derrubando árvore para extrair madeira.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo até uma árvore para cortar.")

                return self._wander(agent_pos, blocked_coords, "Procurando florestas para cortar.")
                    
            elif agent_type == 'builder':
                if inv.get('logs', 0) < 2 and self.inventory_sys.can_carry_fence(inv):
                    self.agent_states[agent_id] = "SEEK_LOGS"
                    
                    my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                    active_boycotts = [wc_id for wc_id, tick_banned in my_boycotts.items() if current_tick - tick_banned < 50]
                    
                    woodcutters = [p for p in radar_data.get('other_agents', []) if p['type'] == 'woodcutter' and p['id'] not in active_boycotts]
                    
                    if woodcutters:
                        target_wc = woodcutters[0]
                        if target_wc['dist'] <= 3:
                            return ("TRADE_LOGS", agent_pos[0], agent_pos[1], target_wc['id'], f"Negociando compra de madeira com {target_wc['name']}.")
                        return self._move_towards(agent_pos, (target_wc['x'], target_wc['z']), blocked_coords, f"Indo comprar madeira de {target_wc['name']}.")
                    else:
                        return self._wander(agent_pos, blocked_coords, "Madeira está muito cara ou em falta. Esperando o mercado acalmar.")

                if inv.get('logs', 0) >= 2 and self.inventory_sys.can_carry_fence(inv):
                    self.agent_states[agent_id] = "CRAFTING"
                    return ("CRAFT_FENCE", agent_pos[0], agent_pos[1], None, "Transformando 2 troncos numa cerca.")

                if inv.get('fences', 0) > 0 and radar_data.get('broken_fences'):
                    self.agent_states[agent_id] = "BUILDING"
                    target = radar_data['broken_fences'][0]
                    if target['dist'] <= 3:
                        return ("REPAIR_FENCE", agent_pos[0], agent_pos[1], target['id'], "Reparando estrutura danificada.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Deslocando para reparo.")
                
                return self._wander(agent_pos, blocked_coords, "Sem matéria-prima ou contratos. Explorando.")
                    
            elif agent_type == 'farmer' and self.inventory_sys.has_seeds(inv):
                self.agent_states[agent_id] = "FARMER"
                
                # 1. PRIORIDADE LOCAL: Se há comida madura AO ALCANCE, colhe primeiro para limpar o terreno
                if radar_data.get('food_ready'):
                    target = radar_data['food_ready'][0]
                    if target['dist'] <= 3:
                        return ("HARVEST", agent_pos[0], agent_pos[1], target['tile_id'], "Limpando terreno: Colhendo batata madura.")

                # 2. GESTÃO DE PROPRIEDADE: Se não tem terreno, tenta planejar um
                if not agent.get('owns_plot'):
                    
                    # === NOVO: LEI DE ZONEAMENTO (Margem de Segurança) ===
                    # Calcula uma "zona invisível" de 1 bloco (+2 metros) ao redor de cada terreno
                    restricted_plot_coords = set()
                    for p in world_plots:
                        p_start_x = p['startX']
                        p_start_z = p['startZ']
                        p_max_x = p_start_x + (p['width'] - 1) * 2
                        p_max_z = p_start_z + (p['height'] - 1) * 2
                        
                        # O range vai do (início - 2) até (fim + 2). O +3 é porque o Python ignora o último número.
                        for x in range(p_start_x - 2, p_max_x + 3, 2):
                            for z in range(p_start_z - 2, p_max_z + 3, 2):
                                restricted_plot_coords.add((x, z))
                    
                   # === NOVO: Varredura SATÉLITE Completa ===
                    sacred_coords = set()
                    for t in world_tiles:
                        # 1. Protege terras que já foram aradas (mesmo sem batatas)
                        if t.get('type') == 'farm':
                            sacred_coords.add((int(t['x']), int(t['z'])))
                            continue
                            
                        # 2. Protege grama com batatas selvagens
                        if t.get('cropsJSON'):
                            try:
                                crops = json.loads(t['cropsJSON'])
                                if len(crops) > 0:
                                    sacred_coords.add((int(t['x']), int(t['z'])))
                            except:
                                pass
                    
                    # Passamos TUDO para o arquiteto: obstáculos, terras aradas/plantadas e recuo!
                    blueprint = self.farm_planner.plan_new_farm(agent_pos, blocked_coords, sacred_coords, restricted_plot_coords)
                    
                    if blueprint:
                        contains_wild_potato = False
                        for cx, cz in sacred_coords:
                            if (cx, cz) in [(int(n[0]), int(n[1])) for n in blueprint['arable_lands']]:
                                contains_wild_potato = True
                                break
                        
                        msg = "Sorte! Envelopou terra fértil no novo terreno!" if contains_wild_potato else "Reivindicou terreno para nova fazenda!"
                        return ("RESERVE_PLOT", blueprint['startX'], blueprint['startZ'], blueprint, msg)
                    
                    if radar_data.get('food_ready'):
                        target = radar_data['food_ready'][0]
                        return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo buscar batata para liberar espaço de plantio.")
                    
                    return self._wander(agent_pos, blocked_coords, "Procurando área livre (com recuo) para expandir.")

                # 3. TRABALHO DE CAMPO: Se já tem terreno, executa o ciclo agrícola
                
                # === NOVA LÓGICA MAS: O Agente calcula o miolo do seu próprio terreno ===
                my_plot = next((p for p in world_plots if p.get('ownerId') == agent_id), None)
                my_interior_coords = set()
                
                if my_plot:
                    p_start_x = my_plot['startX']
                    p_start_z = my_plot['startZ']
                    # Calcula o limite máximo do lote
                    p_max_x = p_start_x + (my_plot['width'] - 1) * 2
                    p_max_z = p_start_z + (my_plot['height'] - 1) * 2
                    
                    # Gera a matriz apenas do interior (amarelo), ignorando as bordas (azul)
                    for x in range(p_start_x + 2, p_max_x, 2):
                        for z in range(p_start_z + 2, p_max_z, 2):
                            my_interior_coords.add((x, z))

                # Filtra a visão do agente para agir APENAS se a terra estiver dentro do miolo
                valid_empty_farms = [f for f in radar_data.get('empty_farms', []) if (int(f['x']), int(f['z'])) in my_interior_coords]
                valid_arable_land = [f for f in radar_data.get('arable_land', []) if (int(f['x']), int(f['z'])) in my_interior_coords]

                # A) Plantar em terras já aradas (Filtrado)
                if valid_empty_farms:
                    target = random.choice(valid_empty_farms[:3])
                    if target['dist'] <= 3:
                        return ("PLANT", agent_pos[0], agent_pos[1], target['id'], "Plantando sementes no meu terreno.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo até área arada para plantar.")
                
                # B) Consultar memória de terras aradas (Blindado contra memórias fora do lote)
                farm_mem = self.memory_sys.get_best_farm_location(agent_id, agent_pos)
                if farm_mem and (int(farm_mem[0]), int(farm_mem[1])) in my_interior_coords:
                    dist = math.hypot(farm_mem[0] - agent_pos[0], farm_mem[1] - agent_pos[1])
                    if dist <= 3:
                        self.memory_sys.invalidate_farm_memory(agent_id, farm_mem)
                        return self._wander(agent_pos, blocked_coords, "Espaço de memória ocupado. Recalculando...")
                    return self._move_towards(agent_pos, farm_mem, blocked_coords, "Movendo para local arado memorizado.")
                    
                # C) Arar novas terras (Filtrado)
                if valid_arable_land:
                    target = random.choice(valid_arable_land[:3])
                    if target['dist'] <= 3:
                        return ("PLOW", agent_pos[0], agent_pos[1], target['id'], "Arando solo para expandir plantação.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Buscando terreno para arar.")

        # PRIORIDADE 4: Exploração
        self.agent_states[agent_id] = "EXPLORE"
        return self._wander(agent_pos, blocked_coords, None)

    # === O MOTOR DE FÍSICA E ANTI-GHOSTING ===
    def _is_move_valid(self, current, nx, nz, mx, mz, blocked_coords):
        # 1. O Bloco de destino final está ocupado?
        if (round(nx), round(nz)) in blocked_coords:
            return False
            
        # 2. O ponto médio da trajetória está bloqueado?
        # IMPORTANTE: Como os agentes andam de 2 em 2, eles pulavam as junções em movimentos diagonais.
        # Agora verificamos sempre o meio do passo, independentemente da direção!
        mid_x = round(current[0] + mx / 2)
        mid_z = round(current[1] + mz / 2)
        if (mid_x, mid_z) in blocked_coords:
            return False
                
        # 3. Anti-Ghosting DIAGONAL (Quinas fechadas)
        if mx != 0 and mz != 0:
            side_x = (round(current[0] + mx), round(current[1]))
            side_z = (round(current[0]), round(current[1] + mz))
            
            # Só bloqueia se AMBOS os lados estiverem fechados, formando um "V" exato.
            # Se apenas um lado tiver cerca, ele consegue escorregar rente à parede para dobrar a esquina.
            if side_x in blocked_coords and side_z in blocked_coords:
                return False
                
        return True

    # === ALGORITMO DE DESVIO E NAVEGAÇÃO ===
    def _move_towards(self, current, target, blocked_coords, log_msg=None):
        dx = target[0] - current[0]
        dz = target[1] - current[1]
        
        best_x = 2 if dx > 0 else (-2 if dx < 0 else 0)
        best_z = 2 if dz > 0 else (-2 if dz < 0 else 0)
        
        moves_to_try = []
        if best_x != 0 and best_z != 0:
            # Tenta diagonal, se bater em cerca (quina), tenta escorregar reto para o lado
            moves_to_try = [(best_x, best_z), (best_x, 0), (0, best_z)]
        else:
            moves_to_try = [(best_x, best_z)]
            if best_x != 0: moves_to_try.extend([(best_x, 2), (best_x, -2)])
            if best_z != 0: moves_to_try.extend([(2, best_z), (-2, best_z)])
            
        for mx, mz in moves_to_try:
            if mx == 0 and mz == 0: continue
            nx = max(-24, min(24, current[0] + mx))
            nz = max(-24, min(24, current[1] + mz))
            
            if self._is_move_valid(current, nx, nz, mx, mz, blocked_coords):
                return ("MOVE", nx, nz, None, log_msg)
                
        return ("MOVE", current[0], current[1], None, (log_msg or "") + " (Caminho bloqueado!)")
        
    def _wander(self, current, blocked_coords, log_msg=None):
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]
        random.shuffle(moves)
        for mx, mz in moves:
            nx = max(-24, min(24, current[0] + mx))
            nz = max(-24, min(24, current[1] + mz))
            
            if self._is_move_valid(current, nx, nz, mx, mz, blocked_coords):
                return ("MOVE", nx, nz, None, log_msg)
                
        return ("MOVE", current[0], current[1], None, log_msg)