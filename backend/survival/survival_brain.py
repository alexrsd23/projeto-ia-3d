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
                    
                    # === NOVO: Filtra parceiros falidos usando o sistema de boicote ===
                    my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                    active_boycotts = [b_id for b_id, tick in my_boycotts.items() if current_tick - tick < 50]
                    
                    spouses = [
                        p for p in radar_data.get('other_agents', [])
                        if p['type'] == agent_type and p.get('married', False) == True and p.get('sex') == target_sex and p['id'] not in active_boycotts
                    ]
                    
                    if spouses:
                        spouse = spouses[0] 
                        if spouse['dist'] <= 3.0:
                            self.agent_states[agent_id] = "PROCREATING"
                            return ("PROCREATE", agent_pos[0], agent_pos[1], spouse['id'], f"Momento romântico com {spouse['name']}...")
                        else:
                            self.agent_states[agent_id] = "COURTING"
                            return self._move_towards(agent_pos, (spouse['x'], spouse['z']), blocked_coords, f"Indo encontrar {spouse['name']} para ter um filho.")
                        
        # === PRIORIDADE 1: A OPORTUNIDADE DE OURO (LOOT) ===
        # Antes de pensar em fome ou trabalho, se houver um saco morto no chão e ele não tiver um lobo a persegui-lo, ele vai lá ver!
        if agent_type != 'wolf' and radar_data.get('loots'):
            
            # === CORREÇÃO ESTRUTURAL: Filtrar loots que o agente já sabe que não pode carregar ===
            my_ignored_loots = self.memory_sys.agent_memories.get(agent_id, {}).get('ignored_loots', {})
            # Ignora o saco por 100 ticks (~25 segundos). Tempo suficiente para ir embora e fazer outra coisa.
            valid_loots = [l for l in radar_data['loots'] if current_tick - my_ignored_loots.get(l['id'], -999) > 100]
            
            if valid_loots:
                target_loot = valid_loots[0]
                if target_loot['dist'] <= 3.0:
                    self.agent_states[agent_id] = "LOOTING"
                    return ("LOOT", agent_pos[0], agent_pos[1], target_loot['id'], "Vasculhando os pertences caídos no chão.")
                
                # Se não estiver a morrer de fome no exato momento, ele desvia a rota para ir saquear
                if not is_critical:
                    self.agent_states[agent_id] = "SEEK_LOOT"
                    return self._move_towards(agent_pos, (target_loot['x'], target_loot['z']), blocked_coords, "Viu pertences no chão! Indo investigar.")
        
        # === PRIORIDADE 0: AUTO-REGULAÇÃO (Comer) ===
        if hunger < 60.0 and self.inventory_sys.has_food(inv):
            return ("EAT_INVENTORY", agent_pos[0], agent_pos[1], None, "Saciando a fome com as provisões da mochila.")

        # PRIORIDADE 1: FOME REAL
        if is_critical or (is_hungry and not self.inventory_sys.has_food(inv)):
            self.agent_states[agent_id] = "SEEK_FOOD"
            if agent_type == 'farmer':
                
                # A) Instinto de Curto Alcance: Tenta a visão local (Radar)
                if radar_data.get('food_ready'):
                    target = radar_data['food_ready'][0] 
                    if target['dist'] <= 3:
                        return ("HARVEST", agent_pos[0], agent_pos[1], target['tile_id'], "Colhendo batata madura para saciar a fome.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Correndo para colher comida (Radar).")
                
                # B) A BÚSSOLA DO ESTÔMAGO: Volta para casa para procurar/esperar comida
                my_plot = next((p for p in world_plots if p.get('ownerId') == agent_id), None)
                if my_plot:
                    # CORREÇÃO GEOMÉTRICA: Força o Snap to Grid (// 2 * 2) para aterrar num bloco par exato!
                    center_x = (my_plot['startX'] + my_plot['width'] - 1) // 2 * 2
                    center_z = (my_plot['startZ'] + my_plot['height'] - 1) // 2 * 2
                    dist_to_plot = math.hypot(center_x - agent_pos[0], center_z - agent_pos[1])
                    
                    if dist_to_plot > 4.0:
                        return self._move_towards(agent_pos, (center_x, center_z), blocked_coords, "Faminto! Retornando à minha fazenda em busca de comida.")
                    else:
                        # === CORREÇÃO DE ESTADO CRÍTICO (ANTI-INANIÇÃO) ===
                        # Se a fome ainda é apenas moderada (>= 25), ele senta e espera a colheita.
                        # Se for crítica (< 25), ele quebra o acampamento e avança para o Mercado/Hipocampo!
                        if not is_critical:
                            self.agent_states[agent_id] = "WAITING_CROP"
                            return ("MOVE", agent_pos[0], agent_pos[1], None, "Fome moderada. Esperando a colheita crescer na minha fazenda...")

                # C) O Hipocampo: Tenta lembrar de batatas selvagens
                best_mem = self.memory_sys.get_best_food_source(agent_id, agent_pos)
                if best_mem:
                    dist = math.hypot(best_mem[0] - agent_pos[0], best_mem[1] - agent_pos[1])
                    if dist <= 3:
                        self.memory_sys.invalidate_food_memory(agent_id, best_mem)
                        return self._wander(agent_pos, blocked_coords, "Alguém comeu a batata que estava aqui! Procurando...")
                    return self._move_towards(agent_pos, best_mem, blocked_coords, "Lembrando de um local com comida selvagem...")

                # === NOVO: PLANO D (MERCADO INTERNO ENTRE FAZENDEIROS) ===
                # Quebra de monopólio e falência biológica: Tenta comprar de um colega fazendeiro.
                my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                active_boycotts = [f_id for f_id, tick_banned in my_boycotts.items() if current_tick - tick_banned < 50]
                
                peer_farmers = [p for p in radar_data.get('other_agents', []) if p['type'] == 'farmer' and p['id'] not in active_boycotts]
                
                if peer_farmers and inv.get('plobs', 0.0) > 0.0:
                    self.agent_states[agent_id] = "SEEK_TRADE"
                    target_farmer = peer_farmers[0]
                    if target_farmer['dist'] <= 3.0:
                        return ("TRADE", agent_pos[0], agent_pos[1], target_farmer['id'], f"Desesperado! Negociando comida com o colega {target_farmer['name']}.")
                    return self._move_towards(agent_pos, (target_farmer['x'], target_farmer['z']), blocked_coords, f"Perseguindo {target_farmer['name']} para comprar batatas do estoque dele.")

                # E) Sobrevivência Bruta: Vaga pelo mapa rezando para achar algo
                return self._wander(agent_pos, blocked_coords, "Faminto e perdido! Vagueando em busca de recursos ou vendedores.")
            
            else:
                # (Mantenha o código do SEEK_TRADE do Lenhador/Construtor exatamente como estava aqui...)
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
                # 1. Verifica Contrato Ativo
                active_contract = self.memory_sys.agent_memories.get(agent_id, {}).get('active_contract')
                if active_contract:
                    plot_id = active_contract['plot_id']
                    target_plot = next((p for p in world_plots if p['id'] == plot_id), None)
                    
                    if target_plot:
                        p_start_x = target_plot['startX']
                        p_start_z = target_plot['startZ']
                        p_max_x = p_start_x + (target_plot['width'] - 1) * 2
                        p_max_z = p_start_z + (target_plot['height'] - 1) * 2
                        
                        perimeter_coords = []
                        for px in range(p_start_x, p_max_x + 1, 2):
                            for pz in range(p_start_z, p_max_z + 1, 2):
                                if px == p_start_x or px == p_max_x or pz == p_start_z or pz == p_max_z:
                                    perimeter_coords.append((px, pz))
                        
                        built_fences = {(round(e['x']), round(e['z'])) for e in world_entities if e.get('type') in ['fence', 'damaged_fence']}
                        built_gates = {(round(e['x']), round(e['z'])) for e in world_entities if e.get('type') == 'gate'}
                        
                        missing_coords = [c for c in perimeter_coords if c not in built_fences and c not in built_gates]
                        
                        if not missing_coords:
                            return ("FINISH_CONTRACT", agent_pos[0], agent_pos[1], None, "Obra concluída! A fazenda do cliente está 100% protegida.")
                        
                        # === NOVO: MATRIZ DE EXCLUSÃO DE QUINAS ===
                        # Identifica os 4 vértices exatos do lote
                        corners = [
                            (p_start_x, p_start_z),
                            (p_max_x, p_start_z),
                            (p_start_x, p_max_z),
                            (p_max_x, p_max_z)
                        ]
                        
                        needs_gate = len(built_gates) == 0
                        
                        if needs_gate:
                            if inv.get('gates', 0) > 0:
                                self.agent_states[agent_id] = "BUILDING"
                                
                                # Filtra as coordenadas válidas, proibindo a instalação nas quinas
                                valid_gate_coords = [c for c in missing_coords if c not in corners]
                                
                                # Garante centralização visual nas paredes retas
                                target = valid_gate_coords[0] if valid_gate_coords else missing_coords[0]
                                
                                dist = math.hypot(target[0] - agent_pos[0], target[1] - agent_pos[1])
                                if dist <= 3.0:
                                    return ("BUILD_NEW_GATE", agent_pos[0], agent_pos[1], {"x": target[0], "z": target[1], "plot_id": plot_id}, "Instalando o portão principal na lateral do terreno.")
                                return self._move_towards(agent_pos, target, blocked_coords, "Indo instalar o portão do cliente.")
                            else:
                                if inv.get('logs', 0) >= 2 and inv.get('stones', 0) >= 4:
                                    self.agent_states[agent_id] = "CRAFTING"
                                    return ("CRAFT_GATE", agent_pos[0], agent_pos[1], None, "Fabricando Portão (2 Troncos, 4 Pedras).")
                        else:
                            # (O bloco das Cercas continua igual daqui em diante)
                            if inv.get('fences', 0) > 0:
                                self.agent_states[agent_id] = "BUILDING"
                                missing_coords.sort(key=lambda c: math.hypot(c[0]-agent_pos[0], c[1]-agent_pos[1]))
                                target = missing_coords[0]
                                dist = math.hypot(target[0] - agent_pos[0], target[1] - agent_pos[1])
                                if dist <= 3.0:
                                    return ("BUILD_NEW_FENCE", agent_pos[0], agent_pos[1], {"x": target[0], "z": target[1], "plot_id": plot_id}, "Erguendo cerca perimetral.")
                                return self._move_towards(agent_pos, target, blocked_coords, "Indo erguer cerca do contrato.")
                            else:
                                if inv.get('logs', 0) >= 2:
                                    self.agent_states[agent_id] = "CRAFTING"
                                    return ("CRAFT_FENCE", agent_pos[0], agent_pos[1], None, "Fabricando Cerca (2 Troncos).")
                    else:
                        return ("FINISH_CONTRACT", agent_pos[0], agent_pos[1], None, "A fazenda do cliente desapareceu. Obra cancelada.")

                # 2. Logística e Coleta de Materiais (Só aciona se faltar material para a obra acima)
                if inv.get('stones', 0) < 16:
                    if radar_data.get('stones_on_ground'):
                        target = radar_data['stones_on_ground'][0]
                        if target['dist'] <= 3:
                            return ("COLLECT_STONE", agent_pos[0], agent_pos[1], target['id'], "Minerando pedra.")
                        return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo coletar pedra.")
                    else:
                        # === CORREÇÃO: Ele DEVE procurar pedras mesmo se tiver contrato, pois o portão exige! ===
                        self.agent_states[agent_id] = "SEEK_STONES"
                        return self._wander(agent_pos, blocked_coords, "Procurando minérios de pedra no mapa.")

                if inv.get('logs', 0) < 20: # Busca carregar a mochila (Compra em LOTE)
                    self.agent_states[agent_id] = "SEEK_LOGS"
                    my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                    active_boycotts = [w for w, tick in my_boycotts.items() if current_tick - tick < 50]
                    woodcutters = [p for p in radar_data.get('other_agents', []) if p['type'] == 'woodcutter' and p['id'] not in active_boycotts]
                    
                    if woodcutters:
                        target_wc = woodcutters[0]
                        if target_wc['dist'] <= 3:
                            return ("TRADE_LOGS_BULK", agent_pos[0], agent_pos[1], target_wc['id'], f"Comprando madeira em lote de {target_wc['name']}.")
                        return self._move_towards(agent_pos, (target_wc['x'], target_wc['z']), blocked_coords, f"Indo comprar madeira de {target_wc['name']}.")

                # 3. Reparos ou Fabricação de Estoque Frio
                if inv.get('fences', 0) > 0 and radar_data.get('broken_fences'):
                    self.agent_states[agent_id] = "BUILDING"
                    target = radar_data['broken_fences'][0]
                    if target['dist'] <= 3:
                        return ("REPAIR_FENCE", agent_pos[0], agent_pos[1], target['id'], "Reparando estrutura danificada.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Deslocando para reparo.")
                
                return self._wander(agent_pos, blocked_coords, "Mochila cheia. Aguardando novos contratos de obras.")
                    
            elif agent_type == 'farmer':
                # === NOVO: INSTINTO PRIMÁRIO DE FORRAGEAMENTO E CAPITAL SEMENTE ===
                # Um fazendeiro saciado, mas sem sementes, não deve vagar inutilmente.
                # Ele deve priorizar a extração gratuita na natureza antes de gastar capital.
                if not self.inventory_sys.has_seeds(inv):
                    
                    # 1. Visão de Longo Alcance: Existe alguma batata madura no radar completo?
                    if radar_data.get('food_ready'):
                        self.agent_states[agent_id] = "FORAGING"
                        target = radar_data['food_ready'][0]
                        # Se chegou ao alvo, colhe imediatamente
                        if target['dist'] <= 3.0:
                            return ("HARVEST", agent_pos[0], agent_pos[1], target['tile_id'], "Oportunidade! Colhendo recurso selvagem para extrair capital semente.")
                        # Se viu ao longe, avança em direção a ele
                        return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Avançando para colher batata selvagem avistada no horizonte.")
                    
                    # 2. Mercado Secundário: Não há recursos naturais livres, tenta o capital financeiro.
                    if inv.get('plobs', 0.0) > 0.0:
                        self.agent_states[agent_id] = "SEEK_SEED_CAPital"
                        
                        my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                        active_boycotts = [f_id for f_id, tick_banned in my_boycotts.items() if current_tick - tick_banned < 50]
                        
                        peer_farmers = [p for p in radar_data.get('other_agents', []) if p['type'] == 'farmer' and p['id'] not in active_boycotts]
                        
                        if peer_farmers:
                            target_farmer = peer_farmers[0]
                            if target_farmer['dist'] <= 3.0:
                                return ("TRADE", agent_pos[0], agent_pos[1], target_farmer['id'], f"Investindo: Comprando batatas de {target_farmer['name']} para extrair sementes!")
                            return self._move_towards(agent_pos, (target_farmer['x'], target_farmer['z']), blocked_coords, f"Perseguindo {target_farmer['name']} para comprar capital semente.")
                        else:
                            return self._wander(agent_pos, blocked_coords, "Sem sementes e sem recursos visíveis. Procurando vendedores de excedente.")
                    else:
                        return self._wander(agent_pos, blocked_coords, "Falido e sem sementes. Vagando pelo mapa à espera de um milagre.")

                # === TRABALHO NORMAL DE CAMPO ===
                # O código original continua a partir daqui, gerindo o plantio, aragem e planeamento do lote...
                self.agent_states[agent_id] = "FARMER"
                
                # 1. PRIORIDADE LOCAL: Se há comida madura AO ALCANCE (no seu terreno), colhe primeiro
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

                # 3. TRABALHO DE CAMPO: O Agente calcula o miolo do seu próprio terreno
                my_plot = next((p for p in world_plots if p.get('ownerId') == agent_id), None)
                
                if my_plot:
                    p_start_x = my_plot['startX']
                    p_start_z = my_plot['startZ']
                    p_max_x = p_start_x + (my_plot['width'] - 1) * 2
                    p_max_z = p_start_z + (my_plot['height'] - 1) * 2
                    
                    my_interior_coords = set()
                    for x in range(p_start_x + 2, p_max_x, 2):
                        for z in range(p_start_z + 2, p_max_z, 2):
                            my_interior_coords.add((x, z))

                    # Classifica as terras usando a visão absoluta do mundo
                    tiles_dict = {(int(t['x']), int(t['z'])): t for t in world_tiles if t.get('x') is not None}
                    
                    needs_planting = []
                    needs_plowing = []
                    
                    for coord in my_interior_coords:
                        tile = tiles_dict.get(coord)
                        if tile and tile.get('type') == 'farm':
                            crops = []
                            if tile.get('cropsJSON'):
                                try:
                                    crops = json.loads(tile['cropsJSON'])
                                except:
                                    pass
                            if len(crops) < 2:
                                needs_planting.append((coord[0], coord[1], tile['id']))
                        else:
                            # A terra é virgem (não está no DB) ou ainda é 'grass'
                            tile_id = tile['id'] if tile else f"tile-{coord[0]}-{coord[1]}"
                            needs_plowing.append((coord[0], coord[1], tile_id))
                            
                    # === EXECUTA A LISTA DE TAREFAS (Ordem de Prioridade) ===
                    if needs_planting:
                        needs_planting.sort(key=lambda c: math.hypot(c[0]-agent_pos[0], c[1]-agent_pos[1]))
                        target = needs_planting[0]
                        dist = math.hypot(target[0]-agent_pos[0], target[1]-agent_pos[1])
                        if dist <= 3.0:
                            return ("PLANT", agent_pos[0], agent_pos[1], {"id": target[2], "x": target[0], "z": target[1]}, "Semeando batata no meu terreno.")
                        return self._move_towards(agent_pos, (target[0], target[1]), blocked_coords, "Indo para área arada para plantar.")
                        
                    elif needs_plowing:
                        needs_plowing.sort(key=lambda c: math.hypot(c[0]-agent_pos[0], c[1]-agent_pos[1]))
                        target = needs_plowing[0]
                        dist = math.hypot(target[0]-agent_pos[0], target[1]-agent_pos[1])
                        if dist <= 3.0:
                            return ("PLOW", agent_pos[0], agent_pos[1], {"id": target[2], "x": target[0], "z": target[1]}, "Arando solo virgem para expandir plantação.")
                        return self._move_towards(agent_pos, (target[0], target[1]), blocked_coords, "Buscando terreno interno para arar.")
                    else:
                        # === VERIFICAÇÃO DE SEGURANÇA (NOVA OBRA) ===
                        # A fazenda está plantada. Mas já tem o perímetro 100% cercado?
                        perimeter_coords = []
                        for px in range(p_start_x, p_max_x + 1, 2):
                            for pz in range(p_start_z, p_max_z + 1, 2):
                                if px == p_start_x or px == p_max_x or pz == p_start_z or pz == p_max_z:
                                    perimeter_coords.append((px, pz))
                                    
                        fence_coords = {(round(e['x']), round(e['z'])) for e in world_entities if e.get('type') in ['fence', 'gate', 'damaged_fence']}
                        missing_fences = [c for c in perimeter_coords if c not in fence_coords]
                        
                        if missing_fences:
                            # === A CORREÇÃO DE GÊNIO ===
                            # O Fazendeiro verifica se JÁ EXISTE algum construtor no mundo com o contrato da sua fazenda!
                            is_under_construction = False
                            for mem in self.memory_sys.agent_memories.values():
                                contract = mem.get('active_contract')
                                if contract and contract.get('plot_id') == my_plot['id']:
                                    is_under_construction = True
                                    break
                                    
                            if is_under_construction:
                                self.agent_states[agent_id] = "WAITING_BUILDER"
                                return self._wander(agent_pos, blocked_coords, "Obra em andamento! Aguardando o construtor finalizar o serviço.")
                                
                            self.agent_states[agent_id] = "SEEK_BUILDER"
                            
                            # Filtra os construtores que já recusaram obras em outros terrenos
                            my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                            active_boycotts = [b_id for b_id, tick in my_boycotts.items() if current_tick - tick < 50]
                            
                            builders = [p for p in radar_data.get('other_agents', []) if p['type'] == 'builder' and p['id'] not in active_boycotts]
                            
                            if builders:
                                target_builder = builders[0]
                                if target_builder['dist'] <= 3.0:
                                    return ("HIRE_BUILDER", agent_pos[0], agent_pos[1], target_builder['id'], f"Contratando o construtor {target_builder['name']} para cercar a minha propriedade!")
                                return self._move_towards(agent_pos, (target_builder['x'], target_builder['z']), blocked_coords, "Perseguindo construtor para firmar contrato de obra.")
                            else:
                                return self._wander(agent_pos, blocked_coords, "Fazenda plantada! Vagando à procura de um Construtor livre para erguer as cercas.")
                        else:
                            # === LIBERDADE ABSOLUTA ===
                            self.agent_states[agent_id] = "EXPLORE"
                            return self._wander(agent_pos, blocked_coords, "Fazenda 100% plantada e murada! Explorando o mundo livremente.")
                        
            # Fim do bloco "if is_comfortable:" e das profissões

        # =========================================================
        # PRIORIDADE 4: Exploração (O FALLBACK GLOBAL)
        # =========================================================
        # ATENÇÃO À INDENTAÇÃO AQUI! 
        # Este bloco captura todos os agentes que não têm profissão ou não têm
        # condições de trabalhar (ex: falta de sementes), garantindo que
        # NUNHUM agente saia desta função sem retornar uma ação.
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
        # --- ALGORITMO PATHFINDING (BFS/A* Híbrido) PARA DESVIO INTELIGENTE ---
        # Garante que o agente contorne cercas e árvores para alcançar o alvo,
        # erradicando loops de colisão.
        start = (round(current[0]), round(current[1]))
        goal = (round(target[0]), round(target[1]))
        
        queue = [(start, [])]
        visited = set([start])
        
        # Movimentos possíveis na malha (4 retas, 4 diagonais)
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]
        
        nodes_evaluated = 0
        MAX_NODES = 250 # Proteção de CPU: Varre uma área grande o suficiente para contornar qualquer fazenda
        
        while queue and nodes_evaluated < MAX_NODES:
            (cx, cz), path = queue.pop(0)
            nodes_evaluated += 1
            
            # Condição de Sucesso: Chegou perto o suficiente do alvo (raio de coleta <= 3.0, mas checamos <= 2.0 para o passo)
            if math.hypot(goal[0] - cx, goal[1] - cz) <= 2.0:
                if path:
                    return ("MOVE", path[0][0], path[0][1], None, log_msg)
                break # Já está na origem colado ao alvo, cai para o fallback de descolagem
                
            # Heurística A*: Ordena movimentos priorizando a direção matemática do objetivo
            # Isso acelera a busca e gera caminhos naturais (menos robóticos)
            moves.sort(key=lambda m: math.hypot(goal[0] - (cx+m[0]), goal[1] - (cz+m[1])))
            
            for mx, mz in moves:
                nx = max(-24, min(24, cx + mx))
                nz = max(-24, min(24, cz + mz))
                neighbor = (nx, nz)
                
                if neighbor not in visited:
                    # Usa a validação de colisão e anti-ghosting da engine principal
                    if self._is_move_valid((cx, cz), nx, nz, mx, mz, blocked_coords):
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
                        
        # === FALLBACK GULOSO E ANTI-TRAVAMENTO ===
        # Se estourar o limite de nós (labirinto fechado sem saída), tenta forçar a aproximação
        dx = target[0] - current[0]
        dz = target[1] - current[1]
        
        best_x = 2 if dx > 0 else (-2 if dx < 0 else 0)
        best_z = 2 if dz > 0 else (-2 if dz < 0 else 0)
        
        moves_to_try = []
        if best_x != 0 and best_z != 0:
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
                
        # === A CURA DO LOOP ===
        # Se até o caminho reto falhar e ele estiver colado numa parede, ele NÃO pode ficar parado. 
        # Ele aciona o Wander para dar um "passo para trás/lado" e descolar da zona de bloqueio!
        return self._wander(current, blocked_coords, (log_msg or "") + " (Buscando rota alternativa para contornar...)")
        
    def _wander(self, current, blocked_coords, log_msg=None):
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]
        random.shuffle(moves)
        for mx, mz in moves:
            nx = max(-24, min(24, current[0] + mx))
            nz = max(-24, min(24, current[1] + mz))
            
            if self._is_move_valid(current, nx, nz, mx, mz, blocked_coords):
                return ("MOVE", nx, nz, None, log_msg)
                
        return ("MOVE", current[0], current[1], None, log_msg)