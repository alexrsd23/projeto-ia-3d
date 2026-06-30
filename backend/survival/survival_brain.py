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
        self.world_bounds = {"minX": -24, "maxX": 24, "minZ": -24, "maxZ": 24}
        
    def _find_service_provider(self, agent_pos, agent_id, required_type, radar_data, all_agents, active_boycotts):
        """
        Sinal Público Integrado com Filtro de Viabilidade Econômica.
        Retorna (target_dict, is_local_bool).
        """
        valid_global_providers = []
        for a in all_agents:
            if a.get('type') == required_type and a.get('id') not in active_boycotts and a.get('id') != agent_id:
                
                # === CORREÇÃO: O Pulo do Gato (Verificação de Liquidez) ===
                inv = self.inventory_sys.parse(a.get('inventoryJSON', "{}"))
                
                # Se for fazendeiro, EXIGE que possua excedente seguro (mais de 3 batatas) antes de se anunciar
                if required_type == 'farmer' and inv.get('potatoes', 0) <= 3:
                    continue
                # Se for lenhador, exige ter estoque de madeira
                if required_type == 'woodcutter' and inv.get('logs', 0) < 1:
                    continue
                
                valid_global_providers.append(a)

        if not valid_global_providers:
            return None, False

        # 1. Busca Local Otimizada
        valid_ids = {a['id'] for a in valid_global_providers}
        local_providers = [p for p in radar_data.get('other_agents', []) if p['id'] in valid_ids]
        if local_providers:
            return local_providers[0], True
            
        # 2. Ping Global (Telecomunicação/Desespero)
        valid_global_providers.sort(key=lambda v: math.hypot(v.get('x', 0) - agent_pos[0], v.get('z', 0) - agent_pos[1]))
        best = valid_global_providers[0]
        dist = math.hypot(best.get('x', 0) - agent_pos[0], best.get('z', 0) - agent_pos[1])
        
        simulated_radar_node = {
            "id": best['id'], "type": best['type'], 
            "name": best.get('name', 'Agente'), 
            "x": best.get('x', 0), "z": best.get('z', 0), 
            "dist": dist
        }
        return simulated_radar_node, False
            
        return None, False

    def decide_next_move(self, agent, world_entities, world_tiles, world_plots, current_tick, all_agents):
        agent_id = agent['id']
        agent_type = agent.get('type', 'farmer') 
        agent_name = agent.get('name')
        if not agent_name or agent_name == "None":
            agent_name = f"Lobo {agent_id[:4]}" if agent_type == 'wolf' else f"Agente {agent_id[:4]}"
        agent_pos = (agent['x'], agent['z'], agent_id) 
        raw_hunger = agent.get('hunger')
        hunger = float(raw_hunger) if raw_hunger is not None else 100.0
        tool_hp = float(agent.get('toolHp', 100.0))
        
        inv = self.inventory_sys.parse(agent.get('inventoryJSON', "{}"))
        
        radar_data = self.perception_sys.scan_environment(agent_pos, world_entities, world_tiles, all_agents)
        
        # ==============================================================================
        # === TRIAGEM LEGAL E BLINDAGEM ÓPTICA (ANTI-GHOSTING & ANTI-ROUBO) ===
        # ==============================================================================
        # Identifica se o agente possui um contrato ativo para liberar o acesso ao terreno do cliente
        my_contract_plot_id = None
        active_contract = self.memory_sys.agent_memories.get(agent_id, {}).get('active_contract')
        if active_contract:
            my_contract_plot_id = active_contract.get('plot_id')

        def is_coord_forbidden(cx, cz):
            """Verifica se a coordenada pertence a um latifúndio no qual o agente não tem passe livre"""
            for p in world_plots:
                px_min, pz_min = p['startX'], p['startZ']
                px_max = px_min + (p['width'] - 1) * 2
                pz_max = pz_min + (p['height'] - 1) * 2
                
                if px_min <= cx <= px_max and pz_min <= cz <= pz_max:
                    # É proibido se não for o dono E não for o construtor contratado
                    if p.get('ownerId') != agent_id and p.get('id') != my_contract_plot_id:
                        return True
            return False

        # Aplica a cegueira legal: Remove do radar TUDO o que for estático e estiver num lote privado
        keys_to_blindfold = [
            'food_ready', 'food_growing', 'empty_farms', 'arable_land', 
            'trees', 'stones_on_ground', 'loots', 'broken_fences', 'stumps', 'logs_on_ground'
        ]
        
        for key in keys_to_blindfold:
            if key in radar_data:
                # Só retém na visão aquilo que NÃO está em zona proibida
                radar_data[key] = [item for item in radar_data[key] if not is_coord_forbidden(item['x'], item['z'])]
        # ==============================================================================
        
        # O Hipocampo só grava o que é legalmente acessível
        self.memory_sys.update_from_perception(agent_id, radar_data, current_tick)
        
        # ==============================================================================
        # === CORREÇÃO CRÍTICA: FILTRO DE DIREITOS DE PROPRIEDADE (ANTI-ROUBO) ===
        # ==============================================================================
        # O radar é puramente óptico. O córtex precisa processar o que é legalmente acessível.
        # Remove do radar qualquer recurso agrícola que esteja num terreno de terceiros.
        def is_coord_mine_or_wild(cx, cz):
            for p in world_plots:
                px_min, pz_min = p['startX'], p['startZ']
                px_max = px_min + (p['width'] - 1) * 2
                pz_max = pz_min + (p['height'] - 1) * 2
                
                if px_min <= cx <= px_max and pz_min <= cz <= pz_max:
                    # Se está dentro de um terreno, só é válido se o terreno for do agente atual
                    return p.get('ownerId') == agent_id
            return True # Está fora de qualquer terreno (Terra Devoluta/Selvagem)

        # Aplica a triagem legal sobre as intenções de colheita e plantio
        for key in ['food_ready', 'food_growing', 'empty_farms', 'arable_land']:
            if key in radar_data:
                radar_data[key] = [item for item in radar_data[key] if is_coord_mine_or_wild(item['x'], item['z'])]
        # ==============================================================================

        # === MAPEAMENTO DE COLISÕES REFINADO (ALTA PERFORMANCE) ===
        blocked_coords = set()
        solid_types = {'fence', 'gate', 'tree', 'stump', 'cactus', 'wall'}
        
        # Estruturas que se conectam visualmente (Cercas e Portões)
        connectable_types = {'fence', 'gate', 'damaged_fence'}
        connectable_coords = set()
        
        # # === NOVO: VISTO DE TRABALHO (WORK VISA) ===
        # # Identifica se o agente possui um contrato ativo para liberar o acesso ao terreno do cliente
        # my_contract_plot_id = None
        # active_contract = self.memory_sys.agent_memories.get(agent_id, {}).get('active_contract')
        # if active_contract:
        #     my_contract_plot_id = active_contract.get('plot_id')

        # === ZONAS DE EXCLUSÃO ESPACIAL (PROPRIEDADES) ===
        # Exceção Comercial: Agentes que estejam ativamente a tentar comprar (ou os próprios donos) ganham passe livre para pisar os cantos do perímetro e aceder ao mercado.
        is_trading = agent_id in self.agent_states and "TRADE" in self.agent_states[agent_id]
        
        for plot in world_plots:
            # 1. Donos e Contratados têm passe livre imediato
            if plot.get('ownerId') == agent_id or plot.get('id') == my_contract_plot_id or is_trading:
                continue 
                
            p_start_x = plot['startX']
            p_start_z = plot['startZ']
            p_width = plot['width']
            p_height = plot['height']
            
            p_max_x = p_start_x + (p_width - 1) * 2
            p_max_z = p_start_z + (p_height - 1) * 2
            
            # === NOVA LEI DE ZONEAMENTO: PROTOCOLO CATRACA E REPAROS ===
            is_trapped = (p_start_x <= agent_pos[0] <= p_max_x) and (p_start_z <= agent_pos[1] <= p_max_z)
            
            is_repairing = False
            if agent_type == 'builder' and radar_data.get('broken_fences'):
                for bf in radar_data['broken_fences']:
                    if p_start_x <= bf['x'] <= p_max_x and p_start_z <= bf['z'] <= p_max_z:
                        is_repairing = True
                        break
                        
            if is_trapped or is_repairing:
                continue
                
            # Bloqueia o acesso a quem está do lado de fora!
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
                    
                    new_x = max(self.world_bounds['minX'], min(self.world_bounds['maxX'], agent_pos[0] + move_x))
                    new_z = max(self.world_bounds['minZ'], min(self.world_bounds['maxZ'], agent_pos[1] + move_z))
                    
                    # Usa a nova validação segura
                    if self._is_move_valid(agent_pos, new_x, new_z, move_x, move_z, blocked_coords):
                        return ("MOVE", new_x, new_z, None, f"Fugindo em pânico! Lobo detectado a {nearest_wolf['dist']:.1f} blocos!")
                    else:
                        return self._wander(agent_pos, blocked_coords, "Curralado! Tentando achar saída para fugir do predador!")
                    
       # === PRIORIDADE 2: INSTINTO SOCIAL E REPRODUTIVO ===
        if agent_type != 'wolf' and hunger >= 30.0:
            is_married = agent.get('married', False)
            
            # Tipos humanos válidos para relação (exclui wolf e loot)
            human_types = ['farmer', 'woodcutter', 'builder', 'blacksmith', 'character']
            
            if not is_married:
                my_rejections = self.memory_sys.agent_memories.get(agent_id, {}).get('rejections', [])
                
                # CORREÇÃO CRÍTICA: Permite casamento com QUALQUER humano livre, gerando diversidade genética
                potential_partners = [
                    p for p in radar_data.get('other_agents', []) 
                    if p['type'] in human_types and p.get('married', False) == False and p['id'] not in my_rejections
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
                # === ESTADO: AGENTE JÁ É CASADO ===
                agent_memory = self.memory_sys.agent_memories.get(agent_id, {})
                last_baby_tick = agent_memory.get('last_reproduction_tick', -999)
                
                # === 1. PERÍODO REFRATÁRIO (COOLDOWN BIOLÓGICO) ===
                # Impede a metralhadora biológica. Exige um intervalo de 500 ticks entre filhos.
                if current_tick - last_baby_tick < 500:
                    pass # O agente ignora a reprodução e cai na lógica de trabalho/exploração
                else:
                    spouse_id = agent.get('spouse_id')
                    my_boycotts = agent_memory.get('boycotts', {})
                    
                    # === 2. VERIFICAÇÃO DE REJEIÇÃO RECENTE ===
                    # Se o parceiro falhou na gravidez recentemente, dá espaço e foca no trabalho
                    if spouse_id in my_boycotts and current_tick - my_boycotts[spouse_id] < 100:
                        pass
                    elif spouse_id:
                        # === 3. AUTOANÁLISE E AUDITORIA BILATERAL UNIFICADA ===
                        # Dicionário de custos alinhado estritamente com o engine.py
                        resource_map = {
                            'farmer': ('potatoes', 2),
                            'woodcutter': ('logs', 5),
                            'builder': ('stones', 4),
                            'blacksmith': ('metal_parts', 2),
                            'wolf': ('none', 0),
                            'character': ('none', 0)
                        }
                        
                        my_kids = agent_memory.get('children_count', 0)
                        my_mult = 2 ** my_kids
                        my_item, my_base_cost = resource_map.get(agent_type, ('potatoes', 2))
                        my_cost = my_base_cost * my_mult
                        
                        my_plobs = inv.get('plobs', 0.0)
                        # A trava de liquidez inegociável de 250 plobs para si mesmo
                        my_funds_ok = my_plobs >= 250.0
                        my_mats_ok = inv.get(my_item, 0) >= my_cost if my_item != 'none' else True
                        
                        if hunger >= 70.0 and my_funds_ok and my_mats_ok:
                            my_spouse = next((p for p in all_agents if p['id'] == spouse_id), None)
                            
                            if my_spouse:
                                spouse_inv = self.inventory_sys.parse(my_spouse.get('inventoryJSON', "{}"))
                                spouse_mem = self.memory_sys.agent_memories.get(spouse_id, {})
                                
                                spouse_kids = spouse_mem.get('children_count', 0)
                                spouse_mult = 2 ** spouse_kids
                                spouse_item, spouse_base_cost = resource_map.get(my_spouse.get('type'), ('potatoes', 2))
                                spouse_cost = spouse_base_cost * spouse_mult
                                
                                # A trava de liquidez inegociável de 250 plobs para o parceiro
                                spouse_funds_ok = spouse_inv.get('plobs', 0.0) >= 250.0
                                spouse_mats_ok = spouse_inv.get(spouse_item, 0) >= spouse_cost if spouse_item != 'none' else True
                                
                                if spouse_funds_ok and spouse_mats_ok:
                                    dist = math.hypot(my_spouse.get('x', 0) - agent_pos[0], my_spouse.get('z', 0) - agent_pos[1])
                                    
                                    if dist <= 3.0:
                                        self.agent_states[agent_id] = "PROCREATING"
                                        return ("PROCREATE", agent_pos[0], agent_pos[1], my_spouse['id'], f"Gerando herdeiro com {my_spouse.get('name')}! (Ambos têm >250 Plobs e materiais)")
                                    else:
                                        self.agent_states[agent_id] = "SEEK_SPOUSE"
                                        return self._move_towards(agent_pos, (my_spouse.get('x', 0), my_spouse.get('z', 0)), blocked_coords, f"Indo ao encontro de {my_spouse.get('name')} para expandir a família.")
                        else:
                            # Caso o cônjuge tenha morrido, o sistema de luto/viuvez tratará de resetar o 'married' para False 
                            # no final do processamento do motor, permitindo um novo casamento no futuro.
                            pass
                        
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
        
        # ==============================================================================
        # === PRIORIDADE 1.2: A CORRIDA DO OURO IMOBILIÁRIA (USUCAPIÃO) ===
        # ==============================================================================
        # O comportamento SÓ PROCESSA DADOS se existirem terrenos na lista 'abandoned'.
        # Caso contrário, ignora a etapa e não consome CPU.
        abandoned_plots = [p for p in world_plots if p.get('status') == 'abandoned']
        
        # CORREÇÃO: Apenas Fazendeiros (agentes com a mecânica agrícola) têm competência legal e técnica para usucapir.
        if abandoned_plots and agent_type == 'farmer':
            # Encontra as terras livres mais próximas
            abandoned_plots.sort(key=lambda p: math.hypot(p['startX'] - agent_pos[0], p['startZ'] - agent_pos[1]))
            target_plot = abandoned_plots[0]
            
            # O alvo é a esquina do terreno
            dist_to_plot = math.hypot(target_plot['startX'] - agent_pos[0], target_plot['startZ'] - agent_pos[1])
            
            if dist_to_plot <= 4.0:
                self.agent_states[agent_id] = "CLAIMING_LAND"
                return ("CLAIM_PLOT", agent_pos[0], agent_pos[1], target_plot['id'], "Cravando a bandeira! Assumindo posse legal das terras por Usucapião.")
            else:
                self.agent_states[agent_id] = "LAND_RUSH"
                return self._move_towards(agent_pos, (target_plot['startX'], target_plot['startZ']), blocked_coords, "Corrida do Ouro! Indo reivindicar terras abandonadas no mapa.")
        # ==============================================================================
        
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
                my_plots = [p for p in world_plots if p.get('ownerId') == agent_id]
                if my_plots:
                    # Identifica a propriedade mais próxima para economizar calorias na viagem
                    my_plot = min(my_plots, key=lambda p: math.hypot(p['startX'] - agent_pos[0], p['startZ'] - agent_pos[1]))
                    
                    # CORREÇÃO GEOMÉTRICA: Força o Snap to Grid (// 2 * 2) para aterrar num bloco par exato!
                    center_x = (my_plot['startX'] + my_plot['width'] - 1) // 2 * 2
                    center_z = (my_plot['startZ'] + my_plot['height'] - 1) // 2 * 2
                    dist_to_plot = math.hypot(center_x - agent_pos[0], center_z - agent_pos[1])
                    
                    if dist_to_plot > 4.0:
                        return self._move_towards(agent_pos, (center_x, center_z), blocked_coords, "Faminto! Retornando a uma das minhas propriedades em busca de comida.")
                    else:
                        if not is_critical:
                            self.agent_states[agent_id] = "WAITING_CROP"
                            return ("MOVE", agent_pos[0], agent_pos[1], None, "Fome moderada. Esperando a colheita crescer no meu latifúndio...")

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
                
                # CORREÇÃO: Utiliza o filtro global de viabilidade (agora não interroga quem não tem batatas)
                target_farmer, is_local = self._find_service_provider(agent_pos, agent_id, 'farmer', radar_data, all_agents, active_boycotts)
                
                if target_farmer and inv.get('plobs', 0.0) > 0.0:
                    self.agent_states[agent_id] = "SEEK_TRADE"
                    if target_farmer['dist'] <= 3.0:
                        return ("TRADE", agent_pos[0], agent_pos[1], target_farmer['id'], f"Desesperado! Negociando comida com o colega {target_farmer['name']}.")
                    return self._move_towards(agent_pos, (target_farmer['x'], target_farmer['z']), blocked_coords, f"Perseguindo {target_farmer['name']} para comprar batatas do estoque dele.")

                # E) Sobrevivência Bruta: Vaga pelo mapa rezando para achar algo
                return self._wander(agent_pos, blocked_coords, "Faminto e perdido! Vagueando em busca de recursos selvagens ou vendedores válidos.")
            
            else:
                # (Mantenha o código do SEEK_TRADE do Lenhador/Construtor exatamente como estava aqui...)
                self.agent_states[agent_id] = "SEEK_TRADE"
                
                my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                active_boycotts = [f_id for f_id, tick_banned in my_boycotts.items() if current_tick - tick_banned < 50]
                
                # Invoca o protocolo de Mercado Global
                target_farmer, is_local = self._find_service_provider(agent_pos, agent_id, 'farmer', radar_data, all_agents, active_boycotts)
                
                if target_farmer and inv.get('plobs', 0.0) > 0.0:
                    if target_farmer['dist'] <= 3.0:
                        return ("TRADE", agent_pos[0], agent_pos[1], target_farmer['id'], f"Desesperado! Iniciando leilão bilateral por comida com {target_farmer['name']}.")
                    
                    msg_log = f"Aproximando-se de {target_farmer['name']} para comprar comida." if is_local else f"📡 RÁDIO GLOBAL | {agent_name}: 'Ameaça de inanição! Compro batatas a qualquer preço!' | 📻 {target_farmer['name']} (X:{target_farmer['x']}, Z:{target_farmer['z']}): 'Venha ao meu terreno negociar!'"
                    return self._move_towards(agent_pos, (target_farmer['x'], target_farmer['z']), blocked_coords, msg_log)
                else:
                    return self._wander(agent_pos, blocked_coords, "Inflação severa ou ausência total de fornecedores ativos. Risco de inanição.")
                
        # === PRIORIDADE 1.5: MANUTENÇÃO DE FERRAMENTAS ===
        if agent_type in ['farmer', 'woodcutter', 'builder'] and tool_hp <= 0.0:
            self.agent_states[agent_id] = "BROKEN_TOOL"
            
            my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
            active_boycotts = [b for b, tick in my_boycotts.items() if current_tick - tick < 50]
            
            # Invoca o protocolo de Sinal Global para Manutenção
            target_smith, is_local = self._find_service_provider(agent_pos, agent_id, 'blacksmith', radar_data, all_agents, active_boycotts)
            
            if target_smith:
                if target_smith['dist'] <= 3.0:
                    tool_n = "Enxada" if agent_type == 'farmer' else ("Machado" if agent_type == 'woodcutter' else "Martelo")
                    return ("REQUEST_REPAIR", agent_pos[0], agent_pos[1], target_smith['id'], f"O {tool_n} quebrou! Solicitando reparo a {target_smith['name']}.")
                
                msg_log = f"Indo consertar a ferramenta com {target_smith['name']}." if is_local else f"📡 RÁDIO GLOBAL | {agent_name}: 'S.O.S! Ferramenta quebrada!' | 📻 {target_smith['name']} (X:{target_smith['x']}, Z:{target_smith['z']}): 'Pode vir à forja, estou livre!'"
                return self._move_towards(agent_pos, (target_smith['x'], target_smith['z']), blocked_coords, msg_log)
            else:
                return self._wander(agent_pos, blocked_coords, "Ferramenta quebrada! Nenhum Ferreiro respondendo ao rádio...")

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
                
                # Coleta de troncos caídos é prioridade (Limpar o chão)
                if radar_data.get('logs_on_ground'):
                    self.agent_states[agent_id] = "COLLECTING"
                    target = radar_data['logs_on_ground'][0]
                    if target['dist'] <= 3:
                        return ("COLLECT_LOG", agent_pos[0], agent_pos[1], target['id'], "Apanhando tronco do chão para a mochila.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo recolher um tronco caído.")

                # === 1. MODO REFLORESTAMENTO INTELIGENTE (Cura e Dispersão) ===
                if inv.get('tree_seed', 0) > 0:
                    
                    # A) Prioridade Absoluta: Replantar em Tocos no radar visual
                    if radar_data.get('stumps'):
                        self.agent_states[agent_id] = "REFORESTING"
                        
                        # MELHORIA: Ordena para focar no toco mais próximo, evitando viagens longas desnecessárias
                        stumps_sorted = sorted(radar_data['stumps'], key=lambda s: s['dist'])
                        target_stump = stumps_sorted[0]
                        
                        if target_stump['dist'] <= 3.0:
                            return ("REPLACE_STUMP", agent_pos[0], agent_pos[1], {"x": target_stump['x'], "z": target_stump['z'], "stump_id": target_stump['id']}, "Extraindo toco morto e plantando nova muda no mesmo local.")
                        return self._move_towards(agent_pos, (target_stump['x'], target_stump['z']), blocked_coords, "Indo revitalizar a área de um toco cortado.")
                    
                    # B) Dispersão em Terra Livre: Se não há tocos visíveis, planta numa coordenada segura
                    # Rola o dado para não despejar tudo de uma vez, ou planta forçosamente se houver extinção total.
                    trees_alive = len(radar_data.get('trees', []))
                    if trees_alive == 0 or random.random() < 0.20:
                        self.agent_states[agent_id] = "SCATTERING_SEEDS"
                        
                        # === LÊ DIRETAMENTE DA CACHE GLOBAL DO MOTOR (Mantido para respeitar as propriedades) ===
                        restricted_plot_coords = getattr(self, 'global_restricted_coords', set())
                        for p in world_plots:
                            p_start_x = p['startX']
                            p_start_z = p['startZ']
                            p_max_x = p_start_x + (p['width'] - 1) * 2
                            p_max_z = p_start_z + (p['height'] - 1) * 2
                            
                            for x in range(p_start_x - 2, p_max_x + 3, 2):
                                for z in range(p_start_z - 2, p_max_z + 3, 2):
                                    restricted_plot_coords.add((x, z))
                        
                        # Carrega todas as árvores para evitar o plantio "em fila" (Mantido do Código 1)
                        existing_trees = [(e.get('x'), e.get('z')) for e in world_entities if e.get('type') in ['tree', 'stump']]
                        
                        # Vetores de movimento possíveis a partir do agente
                        moves = [(0, -2), (0, 2), (-2, 0), (2, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]
                        random.shuffle(moves)
                        
                        for mx, mz in moves:
                            nx = max(self.world_bounds['minX'], min(self.world_bounds['maxX'], agent_pos[0] + mx))
                            nz = max(self.world_bounds['minZ'], min(self.world_bounds['maxZ'], agent_pos[1] + mz))
                            
                            # Condição de Solidez e Proteção Agrícola
                            if (nx, nz) not in blocked_coords and (nx, nz) not in restricted_plot_coords:
                                # Prevenção de Enfileiramento: Avalia a vizinhança na mesma linha/coluna
                                alignment = sum(1 for tx, tz in existing_trees if (tx == nx or tz == nz) and math.hypot(tx-nx, tz-nz) < 10)
                                if alignment < 2:
                                    return ("PLANT_TREE", agent_pos[0], agent_pos[1], {"x": nx, "z": nz}, "Espalhando semente selvagem fora das propriedades.")
                        
                        # Se todas as direções imediatas estão bloqueadas, deambula até achar clareira
                        return self._wander(agent_pos, blocked_coords, "Procurando clareira fértil para plantar (afastado de fazendas e obstáculos).")

                # 2. Trabalho de campo clássico (Corte)
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

                # === 3. DESMATAMENTO TOTAL: A HORA DE GASTAR DINHEIRO ===
                # Se não há árvores, nem troncos, e a mochila não está cheia:
                self.agent_states[agent_id] = "SEEK_SEED"
                my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                active_boycotts = [b for b, tick in my_boycotts.items() if current_tick - tick < 50]
                
                # Invoca o protocolo de Sinal Global B2B (Lenhador -> Ferreiro)
                target_smith, is_local = self._find_service_provider(agent_pos, agent_id, 'blacksmith', radar_data, all_agents, active_boycotts)
                
                if target_smith:
                    if target_smith['dist'] <= 3.0:
                        return ("TRADE_TREE_SEED", agent_pos[0], agent_pos[1], target_smith['id'], f"Floresta vazia! Comprando Kits de Plantio de {target_smith['name']}.")
                    
                    msg_log = f"Indo comprar sementes de {target_smith['name']}." if is_local else f"📡 RÁDIO GLOBAL | {agent_name}: 'A floresta acabou, procuro kits de plantio!' | 📻 {target_smith['name']} (X:{target_smith['x']}, Z:{target_smith['z']}): 'A forja tem estoque!'"
                    return self._move_towards(agent_pos, (target_smith['x'], target_smith['z']), blocked_coords, msg_log)
                
                return self._wander(agent_pos, blocked_coords, "A floresta foi dizimada. Nenhum Ferreiro detectado na rede global para fornecer sementes.")
                    
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
                            # === PROTOCOLO DE EVACUAÇÃO DE OBRA ===
                            # A obra está pronta, mas o contrato SÓ expira quando ele estiver na rua!
                            is_inside = (p_start_x <= agent_pos[0] <= p_max_x) and (p_start_z <= agent_pos[1] <= p_max_z)
                            
                            if is_inside:
                                self.agent_states[agent_id] = "LEAVING_SITE"
                                exterior_nodes = []
                                
                                # Varre os portões recém-instalados para achar uma coordenada vizinha lá fora
                                for gx, gz in built_gates:
                                    for dx, dz in [(2,0), (-2,0), (0,2), (0,-2)]:
                                        nx, nz = gx+dx, gz+dz
                                        # Se a coordenada limítrofe estiver ESTRITAMENTE fora da propriedade
                                        if not (p_start_x <= nx <= p_max_x and p_start_z <= nz <= p_max_z):
                                            if (nx, nz) not in blocked_coords:
                                                exterior_nodes.append((nx, nz))
                                                
                                if exterior_nodes:
                                    # Pega a calçada livre mais próxima do portão e direciona-se a ela
                                    exterior_nodes.sort(key=lambda c: math.hypot(c[0]-agent_pos[0], c[1]-agent_pos[1]))
                                    return self._move_towards(agent_pos, exterior_nodes[0], blocked_coords, "Obra concluída! Evacuando o terreno do cliente pelo portão de saída...")
                                else:
                                    # Fallback dinâmico: Anda até esbarrar na saída
                                    return self._wander(agent_pos, blocked_coords, "Obra concluída! Procurando saída do terreno...")
                            else:
                                # O agente está fisicamente fora da zona restrita! Pode rasgar o contrato.
                                return ("FINISH_CONTRACT", agent_pos[0], agent_pos[1], None, "Obra concluída e terreno evacuado! A fazenda do cliente está 100% protegida.")
                        
                       # === NOVO: MATRIZ DE EXCLUSÃO DE QUINAS ===
                        # Identifica os 4 vértices exatos do lote
                        corners = [
                            (p_start_x, p_start_z),
                            (p_max_x, p_start_z),
                            (p_start_x, p_max_z),
                            (p_max_x, p_max_z)
                        ]
                        
                        # =====================================================================
                        # === CORREÇÃO CRÍTICA: AUDITORIA DE ESCOPO ESPACIAL (ANTI-SELO) ===
                        # =====================================================================
                        # Avalia exclusivamente se ESTE perímetro específico possui um portão,
                        # em vez de perguntar se existe algum portão no mundo inteiro.
                        plot_gates = [c for c in perimeter_coords if c in built_gates]
                        needs_gate = len(plot_gates) == 0
                        
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
                                if inv.get('logs', 0) >= 2 and inv.get('stones', 0) >= 1 and inv.get('metal_parts', 0) >= 2:
                                    self.agent_states[agent_id] = "CRAFTING"
                                    return ("CRAFT_GATE", agent_pos[0], agent_pos[1], None, "Fabricando Portão (2 Troncos, 1 Pedra, 2 Peças Metálicas).")
                                elif inv.get('metal_parts', 0) < 2:
                                    # Interrompe tudo e vai procurar um ferreiro!
                                    self.agent_states[agent_id] = "SEEK_METAL"
                                    my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                                    active_boycotts = [b for b, tick in my_boycotts.items() if current_tick - tick < 50]
                                    
                                    # Invoca o protocolo de Sinal Global B2B (Construtor -> Ferreiro)
                                    target_smith, is_local = self._find_service_provider(agent_pos, agent_id, 'blacksmith', radar_data, all_agents, active_boycotts)
                                    
                                    if target_smith:
                                        if target_smith['dist'] <= 3:
                                            return ("TRADE_METAL_PARTS", agent_pos[0], agent_pos[1], target_smith['id'], f"Comprando Peças Metálicas de {target_smith['name']}.")
                                        
                                        msg_log = f"Indo adquirir metal de {target_smith['name']}." if is_local else f"📡 RÁDIO GLOBAL | {agent_name}: 'Encomenda: Preciso de metais para o portão!' | 📻 {target_smith['name']} (X:{target_smith['x']}, Z:{target_smith['z']}): 'Metal pronto!'"
                                        return self._move_towards(agent_pos, (target_smith['x'], target_smith['z']), blocked_coords, msg_log)
                                    else:
                                        return self._wander(agent_pos, blocked_coords, "Obra parada por falta de metal! Nenhum Ferreiro acessível na rede.")
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
                    
                    # Invoca o protocolo de Sinal Global B2B (Construtor -> Lenhador)
                    target_wc, is_local = self._find_service_provider(agent_pos, agent_id, 'woodcutter', radar_data, all_agents, active_boycotts)
                    
                    if target_wc:
                        if target_wc['dist'] <= 3:
                            return ("TRADE_LOGS_BULK", agent_pos[0], agent_pos[1], target_wc['id'], f"Comprando madeira em lote de {target_wc['name']}.")
                        
                        msg_log = f"Indo negociar madeira de {target_wc['name']}." if is_local else f"📡 RÁDIO GLOBAL | {agent_name}: 'Empreitada requer madeira em lote!' | 📻 {target_wc['name']} (X:{target_wc['x']}, Z:{target_wc['z']}): 'Tenho excedente pronto a carregar!'"
                        return self._move_towards(agent_pos, (target_wc['x'], target_wc['z']), blocked_coords, msg_log)

                # 3. Reparos ou Fabricação de Estoque Frio
                if inv.get('fences', 0) > 0 and radar_data.get('broken_fences'):
                    self.agent_states[agent_id] = "BUILDING"
                    target = radar_data['broken_fences'][0]
                    if target['dist'] <= 3:
                        return ("REPAIR_FENCE", agent_pos[0], agent_pos[1], target['id'], "Reparando estrutura danificada.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Deslocando para reparo.")
                
                return self._wander(agent_pos, blocked_coords, "Mochila cheia. Aguardando novos contratos de obras.")
            
            elif agent_type == 'blacksmith':
                if inv.get('metal_parts', 0) >= 10 and inv.get('tree_seed', 0) >= 20:
                    self.agent_states[agent_id] = "FULL_INVENTORY"
                    return self._wander(agent_pos, blocked_coords, "Estoque de forja e sementes cheios. Vagando à espera de clientes.")
                    
                # Prioridade 1: Metal para os construtores
                if inv.get('stones', 0) >= 2 and inv.get('metal_parts', 0) < 10:
                    self.agent_states[agent_id] = "CRAFTING"
                    return ("CRAFT_METAL_PART", agent_pos[0], agent_pos[1], None, "Batendo minério na bigorna para forjar Peças Metálicas.")
                    
                # Prioridade 2: Sementes para os lenhadores
                if inv.get('stones', 0) >= 1 and inv.get('tree_seed', 0) < 20:
                    self.agent_states[agent_id] = "CRAFTING"
                    return ("CRAFT_TREE_SEED", agent_pos[0], agent_pos[1], None, "Triturando minerais químicos para criar Kits de Reflorestamento.")
                    
                self.agent_states[agent_id] = "SEEK_STONES"
                if radar_data.get('stones_on_ground'):
                    target = radar_data['stones_on_ground'][0]
                    if target['dist'] <= 3:
                        return ("COLLECT_STONE", agent_pos[0], agent_pos[1], target['id'], "Extraindo pedra bruta do solo.")
                    return self._move_towards(agent_pos, (target['x'], target['z']), blocked_coords, "Indo coletar pedra bruta.")
                    
                return self._wander(agent_pos, blocked_coords, "Procurando minérios pelo mapa para alimentar a forja.")
                    
            elif agent_type == 'farmer':
                # === NOVO: INSTINTO PRIMÁRIO DE FORRAGEAMENTO E CAPITAL SEMENTE ===
                # Um fazendeiro saciado, mas sem sementes, não deve vagar inutilmente.
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
                    
                    # === NOVA MECÂNICA: O CICLO AGRÍCOLA FECHADO ===
                    # 2. Se ele JÁ TEM batatas no bolso (comprou ou sobrou), ele deve transformá-las em sementes!
                    if self.inventory_sys.has_food(inv):
                        self.agent_states[agent_id] = "CRAFTING"
                        return ("CRAFT_SEED", agent_pos[0], agent_pos[1], None, "Extraindo sementes das batatas do inventário.")

                    # 3. Mercado Secundário: Não tem sementes, não tem batatas e não há nada selvagem. Tenta comprar com dinheiro.
                    if inv.get('plobs', 0.0) > 0.0:
                        self.agent_states[agent_id] = "SEEK_SEED_CAPital"
                        
                        my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                        active_boycotts = [f_id for f_id, tick_banned in my_boycotts.items() if current_tick - tick_banned < 50]
                        
                        # Invoca o protocolo de Sinal Global (Fazendeiro -> Fazendeiro)
                        target_farmer, is_local = self._find_service_provider(agent_pos, agent_id, 'farmer', radar_data, all_agents, active_boycotts)
                        
                        if target_farmer:
                            if target_farmer['dist'] <= 3.0:
                                return ("TRADE", agent_pos[0], agent_pos[1], target_farmer['id'], f"Investindo: Comprando batatas de {target_farmer['name']} para extrair sementes!")
                            
                            msg_log = f"Perseguindo {target_farmer['name']}." if is_local else f"📡 RÁDIO GLOBAL | {agent_name}: 'Falência agrícola! Preciso de sementes urgentes!' | 📻 {target_farmer['name']} (X:{target_farmer['x']}, Z:{target_farmer['z']}): 'Venha comprar os meus excedentes!'"
                            return self._move_towards(agent_pos, (target_farmer['x'], target_farmer['z']), blocked_coords, msg_log)
                        else:
                            return self._wander(agent_pos, blocked_coords, "Sem sementes e sem vendedores ativos no mundo. Procurando alternativas de falência.")
                    else:
                        return self._wander(agent_pos, blocked_coords, "Falido e sem sementes. Vagando pelo mapa à espera de um milagre biológico.")

                # === TRABALHO NORMAL DE CAMPO ===
                self.agent_states[agent_id] = "FARMER"
                
                # 1. PRIORIDADE LOCAL: Se há comida madura AO ALCANCE (no seu terreno), colhe primeiro
                if radar_data.get('food_ready'):
                    target = radar_data['food_ready'][0]
                    if target['dist'] <= 3:
                        return ("HARVEST", agent_pos[0], agent_pos[1], target['tile_id'], "Limpando terreno: Colhendo batata madura.")

                # 2. GESTÃO DE PROPRIEDADE: Se não tem terreno, tenta planejar um
                if not agent.get('owns_plot'):
                    
                    # === LÊ DIRETAMENTE DA CACHE GLOBAL DO MOTOR ===
                    restricted_plot_coords = getattr(self, 'global_restricted_coords', set())
                    
                    # === NOVO: Varredura SATÉLITE Completa ===
                    sacred_coords = set()
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

                # 3. TRABALHO DE CAMPO: O Agente calcula o miolo dos seus latifúndios
                my_plots = [p for p in world_plots if p.get('ownerId') == agent_id]
                
                if my_plots:
                    my_interior_coords = set()
                    
                    # === CORREÇÃO: CAPACIDADE DE MULTIPLAS FAZENDAS (LATIFÚNDIO) ===
                    # O cérebro agora agrega o espaço cultivável de TODAS as propriedades que possui
                    for plot in my_plots:
                        p_start_x = plot['startX']
                        p_start_z = plot['startZ']
                        p_max_x = p_start_x + (plot['width'] - 1) * 2
                        p_max_z = p_start_z + (plot['height'] - 1) * 2
                        
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
                            
                    # === EXECUTA A LISTA DE TAREFAS ===
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
                        return self._move_towards(agent_pos, (target[0], target[1]), blocked_coords, "Buscando terreno interno livre para arar.")
                    else:
                        # Verificação de segurança: todas as fazendas estão cercadas?
                        perimeter_coords = []
                        for plot in my_plots:
                            p_start_x = plot['startX']
                            p_start_z = plot['startZ']
                            p_max_x = p_start_x + (plot['width'] - 1) * 2
                            p_max_z = p_start_z + (plot['height'] - 1) * 2
                            
                            for px in range(p_start_x, p_max_x + 1, 2):
                                for pz in range(p_start_z, p_max_z + 1, 2):
                                    if px == p_start_x or px == p_max_x or pz == p_start_z or pz == p_max_z:
                                        perimeter_coords.append((px, pz))
                                        
                        fence_coords = {(round(e['x']), round(e['z'])) for e in world_entities if e.get('type') in ['fence', 'gate', 'damaged_fence']}
                        missing_fences = [c for c in perimeter_coords if c not in fence_coords]
                        
                        # 1. VERIFICAÇÃO DE INFRAESTRUTURA (CERCAS)
                        if missing_fences:
                            is_under_construction = False
                            
                            # Verifica se já existe um contrato ativo para alguma das minhas propriedades
                            for mem in self.memory_sys.agent_memories.values():
                                contract = mem.get('active_contract')
                                # O construtor contratado está a trabalhar nalguma das fazendas do agente?
                                if contract and any(contract.get('plot_id') == plot['id'] for plot in my_plots):
                                    is_under_construction = True
                                    break

                            # Se a obra já começou, o fazendeiro apenas aguarda por perto
                            if is_under_construction:
                                self.agent_states[agent_id] = "WAITING_BUILDER"
                                return self._wander(agent_pos, blocked_coords, "Obra em andamento! Aguardando o construtor finalizar os meus perímetros.")

                            # 2. PROCURA DE MÃO DE OBRA (CONTRATAÇÃO)
                            self.agent_states[agent_id] = "SEEK_BUILDER"
                            my_boycotts = self.memory_sys.agent_memories.get(agent_id, {}).get('boycotts', {})
                            active_boycotts = [b_id for b_id, tick in my_boycotts.items() if current_tick - tick < 50]

                            target_builder, is_local = self._find_service_provider(agent_pos, agent_id, 'builder', radar_data, all_agents, active_boycotts)

                            if target_builder:
                                # Se o construtor estiver perto (3 unidades), fecha o contrato
                                if target_builder['dist'] <= 3.0:
                                    return ("HIRE_BUILDER", agent_pos[0], agent_pos[1], target_builder['id'], f"Contratando o construtor {target_builder['name']} para finalizar as minhas propriedades!")
                                
                                # Caso contrário, vai até ele (ou usa o rádio se estiver longe)
                                msg_log = "Visualizou o construtor, indo firmar contrato." if is_local else f"📡 RÁDIO GLOBAL | {agent_name}: 'Preciso de um Arquiteto!' | 📻 {target_builder['name']}: 'Estou a caminho!'"
                                return self._move_towards(agent_pos, (target_builder['x'], target_builder['z']), blocked_coords, msg_log)
                            
                            else:
                                # Se ninguém respondeu, ele vaga pela fazenda esperando
                                return self._wander(agent_pos, blocked_coords, "Fazenda plantada! Nenhum construtor disponível no momento. Aguardando...")

                        # 3. MANUTENÇÃO E PATRULHA (ESTADO IDEAL)
                        else:
                            # Se não há cercas faltando, o Fazendeiro entra em modo de vigia da sua propriedade
                            if my_plots:
                                my_plot = my_plots[0]  # Foca-se na sua sede principal
                                center_x = (my_plot['startX'] + my_plot['width'] - 1) // 2 * 2
                                center_z = (my_plot['startZ'] + my_plot['height'] - 1) // 2 * 2
                                dist_to_center = math.hypot(center_x - agent_pos[0], center_z - agent_pos[1])

                                # Se ele estiver muito longe do centro da fazenda (> 6 unidades), ele volta
                                if dist_to_center > 6.0:
                                    self.agent_states[agent_id] = "PATROLLING"
                                    return self._move_towards(agent_pos, (center_x, center_z), blocked_coords, "Retornando para patrulhar as minhas terras.")
                                
                                # Se já estiver na terra dele e tudo estiver ok, ele explora os arredores da própria sede
                                self.agent_states[agent_id] = "EXPLORE"
                                return self._wander(agent_pos, blocked_coords, "Latifúndio 100% protegido! Patrulhando o perímetro da sede.")
                            
                            else:
                                # Caso o agente não tenha terras (improvável para um fazendeiro, mas seguro tratar)
                                self.agent_states[agent_id] = "EXPLORE"
                                return self._wander(agent_pos, blocked_coords, "Sem posses no momento. Explorando o mundo em busca de oportunidades.")

        # =========================================================
        # PRIORIDADE 4: Exploração e Adaptação Social (Mobilidade)
        # =========================================================
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
        # === CORREÇÃO: Puxa os limites do mundo ===
        min_x, max_x = self.world_bounds['minX'], self.world_bounds['maxX']
        min_z, max_z = self.world_bounds['minZ'], self.world_bounds['maxZ']
        
        # --- ALGORITMO PATHFINDING (BFS/A* Híbrido) PARA DESVIO INTELIGENTE ---
        start = (round(current[0]), round(current[1]))
        goal = (round(target[0]), round(target[1]))
        
        queue = [(start, [])]
        visited = set([start])
        
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]
        
        nodes_evaluated = 0
        MAX_NODES = 400 
        
        while queue and nodes_evaluated < MAX_NODES:
            (cx, cz), path = queue.pop(0)
            nodes_evaluated += 1
            
            if math.hypot(goal[0] - cx, goal[1] - cz) <= 2.0:
                if path:
                    return ("MOVE", path[0][0], path[0][1], None, log_msg)
                break 
                
            moves.sort(key=lambda m: math.hypot(goal[0] - (cx+m[0]), goal[1] - (cz+m[1])))
            
            for mx, mz in moves:
                # === CORREÇÃO: Trava dinâmica ===
                nx = max(min_x, min(max_x, cx + mx))
                nz = max(min_z, min(max_z, cz + mz))
                neighbor = (nx, nz)
                
                if neighbor not in visited:
                    if self._is_move_valid((cx, cz), nx, nz, mx, mz, blocked_coords):
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
                        
        # === FALLBACK GULOSO E ANTI-TRAVAMENTO ===
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
            # === CORREÇÃO: Trava dinâmica ===
            nx = max(min_x, min(max_x, current[0] + mx))
            nz = max(min_z, min(max_z, current[1] + mz))
            
            if self._is_move_valid(current, nx, nz, mx, mz, blocked_coords):
                return ("MOVE", nx, nz, None, log_msg)
                
        return self._wander(current, blocked_coords, (log_msg or "") + " (Buscando rota alternativa para contornar...)")
        
    def _wander(self, current, blocked_coords, log_msg=None):
        # === CORREÇÃO: Puxa os limites do mundo ===
        min_x, max_x = self.world_bounds['minX'], self.world_bounds['maxX']
        min_z, max_z = self.world_bounds['minZ'], self.world_bounds['maxZ']
        
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]
        random.shuffle(moves)
        for mx, mz in moves:
            # === CORREÇÃO: Trava dinâmica ===
            nx = max(min_x, min(max_x, current[0] + mx))
            nz = max(min_z, min(max_z, current[1] + mz))
            
            if self._is_move_valid(current, nx, nz, mx, mz, blocked_coords):
                return ("MOVE", nx, nz, None, log_msg)
                
        return ("MOVE", current[0], current[1], None, log_msg)