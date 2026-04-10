import random
import math
from survival.inventory import InventorySystem
from survival.perception import PerceptionSystem
from survival.memory_system import SpatialMemory
from survival.economy_system import EconomySystem
from survival.biology import BiologySystem
from survival.market_intelligence import MarketIntelligence

class SurvivalController:
    def __init__(self):
        self.market_intel = MarketIntelligence(EconomySystem(), BiologySystem())
        self.inventory_sys = InventorySystem()
        self.perception_sys = PerceptionSystem()
        self.memory_sys = SpatialMemory()
        self.agent_states = {} 

    def decide_next_move(self, agent, world_entities, world_tiles, current_tick, all_agents):
        agent_id = agent['id']
        agent_type = agent.get('type', 'farmer') 
        agent_pos = (agent['x'], agent['z'], agent_id) 
        raw_hunger = agent.get('hunger')
        hunger = float(raw_hunger) if raw_hunger is not None else 100.0
        
        inv = self.inventory_sys.parse(agent.get('inventoryJSON', "{}"))
        
        radar_data = self.perception_sys.scan_environment(agent_pos, world_entities, world_tiles, all_agents)
        self.memory_sys.update_from_perception(agent_id, radar_data, current_tick)
        
        # === NOVO: MAPEAMENTO DE COLISÕES (OBSTÁCULOS) ===
        blocked_coords = set()
        for e in world_entities:
            # Humanos e Lobos NÃO atravessam cercas inteiras
            if e['type'] == 'fence':
                blocked_coords.add((e['x'], e['z']))
            # O Lobo TAMBÉM NÃO consegue atravessar portões (Humanos sim, passam livremente!)
            elif e['type'] == 'gate' and agent_type == 'wolf':
                blocked_coords.add((e['x'], e['z']))

        # === ZONAS PSICOLÓGICAS ===
        is_critical = hunger < 25     
        is_hungry = hunger < 60       
        is_comfortable = hunger >= 60 
        needs_stock = self.inventory_sys.needs_replenish(inv)
        
        # === PRIORIDADE ABSOLUTA: INSTINTO DE FUGA (MEDO) ===
        if agent_type != 'wolf':
            wolves = [p for p in radar_data.get('other_agents', []) if p['type'] == 'wolf']
            if wolves:
                nearest_wolf = wolves[0] # O Perception já ordena pelo mais perto
                if nearest_wolf['dist'] <= 5.0: # Raio de Perigo Crítico
                    self.agent_states[agent_id] = "FLEEING"
                    
                    # Calcula a direção OPOSTA ao lobo
                    dx = agent_pos[0] - nearest_wolf['x']
                    dz = agent_pos[1] - nearest_wolf['z']
                    
                    move_x = 2 if dx > 0 else (-2 if dx < 0 else random.choice([-2, 2]))
                    move_z = 2 if dz > 0 else (-2 if dz < 0 else random.choice([-2, 2]))
                    
                    new_x = max(-24, min(24, agent_pos[0] + move_x))
                    new_z = max(-24, min(24, agent_pos[1] + move_z))
                    
                    if (new_x, new_z) not in blocked_coords:
                        return ("MOVE", new_x, new_z, None, f"Fugindo em pânico! Lobo detectado a {nearest_wolf['dist']:.1f} blocos!")
                    else:
                        return self._wander(agent_pos, blocked_coords, "Curralado! Tentando achar saída para fugir do predador!")
        
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
                    if target['dist'] <= 1.5:
                        return ("HARVEST", target['x'], target['z'], target['tile_id'], "Colhendo batata madura.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo colher comida.")
            else:
                self.agent_states[agent_id] = "SEEK_TRADE"
                farmers = [p for p in radar_data.get('other_agents', []) if p['type'] == 'farmer']
                if farmers:
                    target_farmer = farmers[0]
                    if target_farmer['dist'] <= 1.5:
                        return ("TRADE", target_farmer['x'], target_farmer['z'], target_farmer['id'], f"Iniciando negociação de comida com {target_farmer['name']}.")
                    return self._move_towards(agent_pos, (target_farmer['x'], target_farmer['z']), blocked_coords, f"Perseguindo o fazendeiro {target_farmer['name']} para comprar comida.")
                else:
                    return self._wander(agent_pos, blocked_coords, "Com fome, mas não vejo nenhum fazendeiro para comprar batatas. Explorando.")

        # PRIORIDADE 2: TRABALHO
        if is_comfortable:
            will_work = self.market_intel.should_work(agent.get('profession', ''), hunger, agent.get('lieLevel', 0))
            if not will_work:
                self.agent_states[agent_id] = "STRIKE"
                return self._wander(agent_pos, blocked_coords, "Greve: O preço da comida está tão alto que as calorias gastas dariam prejuízo.")

            # 2. Execução da Profissão Específica
            if agent_type == 'woodcutter':
                # ETAPA 1: O chão está sujo de troncos? Recolhe primeiro!
                if radar_data.get('logs_on_ground'):
                    self.agent_states[agent_id] = "COLLECTING"
                    target = radar_data['logs_on_ground'][0]
                    if target['dist'] <= 1.5:
                        return ("COLLECT_LOG", target['x'], target['z'], target['id'], "Apanhando tronco do chão para a mochila.")
                    # === CORREÇÃO: Adicionado blocked_coords ===
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo recolher um tronco caído.")

                # ETAPA 2: O chão está limpo? Então vamos derrubar mais uma árvore!
                self.agent_states[agent_id] = "CHOPPING"
                if radar_data.get('trees'):
                    target = radar_data['trees'][0]
                    if target['dist'] <= 1.5:
                        return ("CHOP_TREE", target['x'], target['z'], target['id'], "Derrubando árvore para extrair madeira.")
                    # === CORREÇÃO: Adicionado blocked_coords ===
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo até uma árvore para cortar.")

                # ETAPA 3: Limite do inventário!
                if not self.inventory_sys.can_collect_log(inv):
                    self.agent_states[agent_id] = "FULL_INVENTORY"
                    return self._wander(agent_pos, blocked_coords, "Mochila de madeira cheia! Vagando até encontrar um comprador.")
                    
            elif agent_type == 'builder':
                if inv.get('logs', 0) < 2 and self.inventory_sys.can_carry_fence(inv):
                    self.agent_states[agent_id] = "SEEK_LOGS"
                    woodcutters = [p for p in radar_data.get('other_agents', []) if p['type'] == 'woodcutter']
                    if woodcutters:
                        target_wc = woodcutters[0]
                        if target_wc['dist'] <= 1.5:
                            return ("TRADE_LOGS", target_wc['x'], target_wc['z'], target_wc['id'], f"Negociando compra de madeira com {target_wc['name']}.")
                        return self._move_towards(agent_pos, (target_wc['x'], target_wc['z']), blocked_coords, f"Indo comprar madeira de {target_wc['name']}.")

                if inv.get('logs', 0) >= 2 and self.inventory_sys.can_carry_fence(inv):
                    self.agent_states[agent_id] = "CRAFTING"
                    return ("CRAFT_FENCE", agent_pos[0], agent_pos[1], None, "Transformando 2 troncos numa cerca.")

                if inv.get('fences', 0) > 0 and radar_data.get('broken_fences'):
                    self.agent_states[agent_id] = "BUILDING"
                    target = radar_data['broken_fences'][0]
                    if target['dist'] <= 1.5:
                        return ("REPAIR_FENCE", target['x'], target['z'], target['id'], "Reparando estrutura danificada.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Deslocando para reparo.")
                
                return self._wander(agent_pos, blocked_coords, "Sem matéria-prima ou contratos. Explorando.")
                    
            elif agent_type == 'farmer' and self.inventory_sys.has_seeds(inv):
                self.agent_states[agent_id] = "FARMER"
                if radar_data.get('empty_farms'):
                    target = random.choice(radar_data['empty_farms'][:3])
                    if target['dist'] <= 1.5:
                        return ("PLANT", target['x'], target['z'], target['id'], "Plantando sementes.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo replantar em terra livre.")
                
                farm_mem = self.memory_sys.get_best_farm_location(agent_id, agent_pos)
                if farm_mem:
                    dist = math.hypot(farm_mem[0] - agent_pos[0], farm_mem[1] - agent_pos[1])
                    if dist <= 1.5:
                        self.memory_sys.invalidate_farm_memory(agent_id, farm_mem)
                        return self._wander(agent_pos, blocked_coords, "Conflito de espaço: Terra lotada. Memória apagada.")
                    return self._move_towards(agent_pos, farm_mem, blocked_coords, "Deslocando para terra previamente arada.")
                    
                if radar_data.get('arable_land'):
                    target = random.choice(radar_data['arable_land'][:3])
                    if target['dist'] <= 1.5:
                        return ("PLOW", target['x'], target['z'], target['id'], "Arando solo virgem.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Buscando terreno virgem para arar.")
                
            # O LOBO
            elif agent_type == 'wolf':
                self.agent_states[agent_id] = "HUNTING"
                preys = [p for p in radar_data.get('other_agents', []) if p['type'] in ['farmer', 'woodcutter', 'builder']]
                if preys:
                    target_prey = preys[0]
                    if target_prey['dist'] <= 1.5:
                        return ("ATTACK_AGENT", target_prey['x'], target_prey['z'], target_prey['id'], f"Atacando {target_prey['name']} (-20 HP)!")
                    
                    if radar_data.get('fences'):
                        target_fence = radar_data['fences'][0]
                        if target_fence['dist'] <= 1.5:
                            return ("ATTACK_FENCE", target_fence['x'], target_fence['z'], target_fence['id'], "Destruindo barreira para alcançar a presa!")

                    return self._move_towards(agent_pos, (target_prey['x'], target_prey['z']), blocked_coords, f"Perseguindo {target_prey['name']}!")
                
                if radar_data.get('fences'):
                    target_fence = radar_data['fences'][0]
                    if target_fence['dist'] <= 1.5:
                        return ("ATTACK_FENCE", target_fence['x'], target_fence['z'], target_fence['id'], "Destruindo uma estrutura por instinto.")
                    return self._move_towards(agent_pos, (target_fence['x'], target_fence['z']), blocked_coords, "Indo investigar uma estrutura para destruir.")

                return self._wander(agent_pos, blocked_coords, "Patrulhando em busca de presas.")

        # PRIORIDADE 3: Colecionador
        if needs_stock and radar_data.get('food_ready'):
            target = radar_data['food_ready'][0] 
            if target['dist'] <= 1.5:
                self.agent_states[agent_id] = "STOCKPILING"
                return ("HARVEST", target['x'], target['z'], target['tile_id'], "Estocagem preventiva.")

        # PRIORIDADE 4: Exploração
        self.agent_states[agent_id] = "EXPLORE"
        return self._wander(agent_pos, blocked_coords, None)

    # === ALGORITMO DE DESVIO DE OBSTÁCULOS (PATHFINDING LEVE) ===
    def _move_towards(self, current, target, blocked_coords, log_msg=None):
        dx = target[0] - current[0]
        dz = target[1] - current[1]
        
        best_x = 2 if dx > 0 else (-2 if dx < 0 else 0)
        best_z = 2 if dz > 0 else (-2 if dz < 0 else 0)
        
        moves_to_try = []
        # Se for um movimento diagonal, tenta os vetores laterais caso bloqueado
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
            
            # Se a coordenada não tiver cerca/portão, mova-se para lá!
            if (nx, nz) not in blocked_coords:
                return ("MOVE", nx, nz, None, log_msg)
                
        # Se todos os caminhos à frente estiverem cercados, ele fica parado a pensar
        return ("MOVE", current[0], current[1], None, (log_msg or "") + " (Caminho bloqueado!)")
        
    def _wander(self, current, blocked_coords, log_msg=None):
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]
        random.shuffle(moves)
        for mx, mz in moves:
            nx = max(-24, min(24, current[0] + mx))
            nz = max(-24, min(24, current[1] + mz))
            if (nx, nz) not in blocked_coords:
                return ("MOVE", nx, nz, None, log_msg)
        return ("MOVE", current[0], current[1], None, log_msg)