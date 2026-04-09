import random
import math
from survival.inventory import InventorySystem
from survival.perception import PerceptionSystem
from survival.memory_system import SpatialMemory

class SurvivalController:
    def __init__(self):
        self.inventory_sys = InventorySystem()
        self.perception_sys = PerceptionSystem()
        self.memory_sys = SpatialMemory()
        self.agent_states = {} # Guarda o estado psicológico do agente

    def decide_next_move(self, agent, world_entities, world_tiles, current_tick):
        agent_id = agent['id']
        agent_pos = (agent['x'], agent['z'])
        hunger = agent.get('hunger', 100)
        inv = self.inventory_sys.parse(agent.get('inventoryJSON', "{}"))
        
        radar_data = self.perception_sys.scan_environment(agent_pos, world_entities, world_tiles)
        self.memory_sys.update_from_perception(agent_id, radar_data, current_tick)
        
        # === AS NOVAS ZONAS PSICOLÓGIDAS ===
        is_critical = hunger < 25     # Risco de Morte: Desespero
        is_hungry = hunger < 60       # Fome Moderada: Procura comida
        is_comfortable = hunger >= 60 # Zona de Conforto: Expansão e Planeamento
        needs_stock = self.inventory_sys.needs_replenish(inv)
        
        # ========================================================
        # PRIORIDADE 0: Auto-Regulação Preventiva (A grande sacada!)
        # Se tem fome moderada, mas tem comida no bolso, come logo um lanche 
        # para voltar à Zona de Conforto e poder continuar a trabalhar sem parar.
        # ========================================================
        # SUBSTITUA TODA A LÓGICA DO decide_next_move A PARTIR DA PRIORIDADE 0
        
        # PRIORIDADE 0: Auto-Regulação Preventiva
        if is_hungry and self.inventory_sys.has_food(inv):
            self.agent_states[agent_id] = "SNACKING"
            log = f"Avaliando necessidades: Fome moderada ({hunger:.1f}%). Consumindo 1 batata preventiva do inventário."
            return ("EAT_INVENTORY", agent_pos[0], agent_pos[1], None, log)
            
        # PRIORIDADE 1: Fome Real -> Busca Racional
        if is_critical or (is_hungry and not self.inventory_sys.has_food(inv)):
            self.agent_states[agent_id] = "SEEK_FOOD"
            
            if radar_data['food_ready']:
                target = radar_data['food_ready'][0] 
                if target['dist'] <= 1.5:
                    log = f"Alvo alcançado: Colhendo batata madura em X:{target['x']} Z:{target['z']}."
                    return ("HARVEST", target['x'], target['z'], target['tile_id'], log)
                
                log = f"Radar detectou batata madura a {target['dist']:.1f} blocos. Iniciando deslocamento para X:{target['x']} Z:{target['z']}."
                return self._move_towards(agent_pos, (target['x'], target['z']), log)
                
            mem_target = self.memory_sys.get_best_food_source(agent_id, agent_pos)
            if mem_target:
                dist = math.hypot(mem_target[0] - agent_pos[0], mem_target[1] - agent_pos[1])
                if dist <= 1.5:
                    self.memory_sys.invalidate_food_memory(agent_id, mem_target)
                    log = f"Decepção: Memória invalidada em X:{mem_target[0]} Z:{mem_target[1]}. Recurso já colhido por concorrência. Buscando alternativas."
                    return self._wander(agent_pos, log)
                
                log = f"Radar limpo. Consultando memória: Alimento provável em X:{mem_target[0]} Z:{mem_target[1]}. Deslocando-se."
                return self._move_towards(agent_pos, mem_target, log)

        # PRIORIDADE 2: O Fazendeiro Estrategista
        if is_comfortable and self.inventory_sys.has_seeds(inv):
            self.agent_states[agent_id] = "FARMER"
            
            if radar_data['empty_farms']:
                target = random.choice(radar_data['empty_farms'][:3])
                if target['dist'] <= 1.5:
                    log = f"Expansão agrícola: Plantando sementes em terra arada (X:{target['x']} Z:{target['z']})."
                    return ("PLANT", target['x'], target['z'], target['id'], log)
                log = f"Estratégia: Sementes disponíveis. Indo replantar em terra livre (X:{target['x']} Z:{target['z']})."
                return self._move_towards(agent_pos, (target['x'], target['z']), log)
            
            farm_mem = self.memory_sys.get_best_farm_location(agent_id, agent_pos)
            if farm_mem:
                dist = math.hypot(farm_mem[0] - agent_pos[0], farm_mem[1] - agent_pos[1])
                if dist <= 1.5:
                    # === A CURA DO LOOP ESTÁ AQUI ===
                    # Ele chegou, a terra está cheia. Ele APAGA a memória para nunca mais voltar aqui hoje.
                    self.memory_sys.invalidate_farm_memory(agent_id, farm_mem)
                    log = f"Conflito de espaço: Terra em X:{farm_mem[0]} Z:{farm_mem[1]} já está lotada. Memória apagada. Buscando nova área."
                    return self._wander(agent_pos, log)
                    
                log = f"Memória agrícola: Deslocando para terra previamente arada em X:{farm_mem[0]} Z:{farm_mem[1]}."
                return self._move_towards(agent_pos, farm_mem, log)
                
            if radar_data['arable_land']:
                target = random.choice(radar_data['arable_land'][:3])
                if target['dist'] <= 1.5:
                    log = f"Pioneirismo: Arando solo virgem em X:{target['x']} Z:{target['z']} para futura fazenda."
                    return ("PLOW", target['x'], target['z'], target['id'], log)
                log = f"Buscando terreno virgem para arar em X:{target['x']} Z:{target['z']}."
                return self._move_towards(agent_pos, (target['x'], target['z']), log)

        # PRIORIDADE 3: Colecionador
        if needs_stock and radar_data['food_ready']:
            target = radar_data['food_ready'][0] 
            if target['dist'] <= 1.5:
                self.agent_states[agent_id] = "STOCKPILING"
                log = f"Estocagem preventiva: Colhendo recurso excedente em X:{target['x']} Z:{target['z']} para a mochila."
                return ("HARVEST", target['x'], target['z'], target['tile_id'], log)

        # PRIORIDADE 4: Exploração de Abundância
        self.agent_states[agent_id] = "EXPLORE"
        # Omitimos log aqui para não floodar quando estão apenas a andar sem rumo, ou enviamos um log passivo
        return self._wander(agent_pos, None)

    def _move_towards(self, current, target, log_msg=None):
        dx = target[0] - current[0]
        dz = target[1] - current[1]
        move_x = 2 if dx > 0 else (-2 if dx < 0 else 0)
        move_z = 2 if dz > 0 else (-2 if dz < 0 else 0)
        new_x = max(-24, min(24, current[0] + move_x))
        new_z = max(-24, min(24, current[1] + move_z))
        return ("MOVE", new_x, new_z, None, log_msg)
        
    def _wander(self, current, log_msg=None):
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        move = random.choice(moves)
        new_x = max(-24, min(24, current[0] + move[0]))
        new_z = max(-24, min(24, current[1] + move[1]))
        return ("MOVE", new_x, new_z, None, log_msg)