import math
import random
import numpy as np

class SharedKnowledgeSystem:
    def __init__(self):
        self.lethal_zones = {} # (x, z) -> {'deaths': int, 'cooldown_until': int}
        self.current_tick = 0

    def tick(self):
        self.current_tick += 1

    def mark_danger(self, x, z):
        coord = (float(x), float(z))
        if coord not in self.lethal_zones:
            # 1ª morte: 150 ticks de bloqueio absoluto (~3 ciclos)
            self.lethal_zones[coord] = {'deaths': 1, 'cooldown_until': self.current_tick + 150} 
        else:
            self.lethal_zones[coord]['deaths'] += 1
            deaths = self.lethal_zones[coord]['deaths']
            # Dobra o tempo de bloqueio a cada morte recorrente: 150, 300, 600...
            cooldown = 150 * (2 ** (deaths - 1))
            self.lethal_zones[coord]['cooldown_until'] = self.current_tick + cooldown

    def is_dangerous(self, x, z):
        coord = (float(x), float(z))
        if coord in self.lethal_zones:
            # Se ainda estiver dentro do tempo de penalidade (cooldown), o perigo está ativo!
            if self.current_tick < self.lethal_zones[coord]['cooldown_until']:
                return True
        return False
        
    def mark_safe(self, x, z):
        coord = (float(x), float(z))
        if coord in self.lethal_zones:
            # Se um agente passou por aqui sem morrer, reduzimos a penalidade
            self.lethal_zones[coord]['deaths'] = max(0, self.lethal_zones[coord]['deaths'] - 1)
            if self.lethal_zones[coord]['deaths'] == 0:
                del self.lethal_zones[coord]

class EventLogSystem:
    def __init__(self):
        self.events = []
        self.counter = 0

    def log(self, level, message):
        self.counter += 1
        self.events.append({
            "id": f"evt-{self.counter}",
            "level": level,
            "message": message,
            "timestamp": "now" 
        })

    def flush(self):
        res = self.events.copy()
        self.events.clear()
        return res

class RouteAnalyticsSystem:
    def __init__(self, logger):
        self.logger = logger
        self.active_episodes = {} 
        self.best_routes = {} 
        self.origin_stats = {} 
        self.leaderboard = {} 

    def start_episode(self, agent_id, origin_x, origin_z):
        origin = (float(origin_x), float(origin_z))
        
        mode = 'explore'
        planned_route = []
        
        if origin in self.best_routes:
            confidence = self.best_routes[origin].get('confidence', 0.85)
            
            # MATEMÁTICA DE SATURAÇÃO (A SUA IDEIA):
            # Se a confiança da rota chegou a 95%, o agente confia cegamente (100% Determinístico)
            eval_confidence = 1.0 if confidence >= 0.95 else confidence
            
            if random.random() < eval_confidence:
                mode = 'exploit'
                planned_route = self.best_routes[origin]['raw_actions']
            
        if agent_id not in self.active_episodes:
            self.active_episodes[agent_id] = {
                'origin': origin,
                'steps': 0,
                'actions': [],
                'raw_actions': [],
                'path_coords': [origin], # Guarda todo o caminho físico
                'mode': mode,
                'planned_route': planned_route
            }

    def get_planned_action(self, agent_id):
        ep = self.active_episodes.get(agent_id)
        if not ep or ep['mode'] != 'exploit': 
            return None
            
        step_idx = ep['steps']
        if step_idx < len(ep['planned_route']):
            return ep['planned_route'][step_idx]
        else:
            ep['mode'] = 'explore'
            return None

    def abort_exploit(self, agent_id):
        if agent_id in self.active_episodes:
            self.active_episodes[agent_id]['mode'] = 'explore'

    # Adicionámos new_x e new_z para desenhar a linha azul depois
    def record_step(self, agent_id, action_idx, new_x, new_z):
        if agent_id in self.active_episodes:
            actions_map = ["CIMA", "BAIXO", "ESQUERDA", "DIREITA"]
            self.active_episodes[agent_id]['steps'] += 1
            self.active_episodes[agent_id]['actions'].append(actions_map[action_idx])
            self.active_episodes[agent_id]['raw_actions'].append(int(action_idx))
            self.active_episodes[agent_id]['path_coords'].append((float(new_x), float(new_z)))

    def finalize_episode(self, agent_id, success, agent_name):
        if agent_id not in self.active_episodes: return
        
        ep = self.active_episodes[agent_id]
        origin = ep['origin']
        
        if origin not in self.origin_stats:
            self.origin_stats[origin] = {'attempts': 0, 'successes': 0}
            
        self.origin_stats[origin]['attempts'] += 1
        
        if success:
            self.origin_stats[origin]['successes'] += 1
            
            if agent_name not in self.leaderboard:
                self.leaderboard[agent_name] = {'successes': 0, 'best_time': 9999}
            self.leaderboard[agent_name]['successes'] += 1
            self.leaderboard[agent_name]['best_time'] = min(self.leaderboard[agent_name]['best_time'], ep['steps'])
            
            score = ep['steps'] 
            
            if origin not in self.best_routes or score < self.best_routes[origin]['score']:
                self.best_routes[origin] = {
                    'score': score,
                    'steps': ep['steps'],
                    'agent_name': agent_name,
                    'actions': ep['actions'],
                    'raw_actions': ep['raw_actions'],
                    'path_coords': ep['path_coords'],
                    'confidence': 0.85, 
                    'fails': 0
                }
            else:
                if self.best_routes[origin]['raw_actions'] == ep['raw_actions']:
                    # Aumenta até bater no teto de 100% de confiança
                    self.best_routes[origin]['confidence'] = min(1.0, self.best_routes[origin].get('confidence', 0.85) + 0.05)
                    self.best_routes[origin]['fails'] = 0
        else:
            if ep['mode'] == 'exploit' and origin in self.best_routes:
                self.best_routes[origin]['fails'] = self.best_routes[origin].get('fails', 0) + 1
                
                # PENALIZAÇÃO AGRESSIVA: Cai 30% a cada morte. Apenas 2 falhas destroem a rota.
                self.best_routes[origin]['confidence'] -= 0.30
                
                if self.best_routes[origin]['fails'] >= 2 or self.best_routes[origin]['confidence'] < 0.30:
                    self.logger.log("WARNING", f"🔄 Rota de X:{origin[0]} Z:{origin[1]} INVALIDADA (Ambiente Dinâmico mudou).")
                    del self.best_routes[origin]

        del self.active_episodes[agent_id]

    def get_telemetry_data(self, shared_knowledge):
        # Mapeia APENAS A ROTA GLOBAL MAIS RÁPIDA (Filtra a aranha de linhas azuis)
        consolidated_paths = []
        best_global_score = float('inf')
        best_global_path = []
        
        for k, v in self.best_routes.items():
            if v.get('confidence', 0) >= 0.90:
                if v['score'] < best_global_score:
                    best_global_score = v['score']
                    best_global_path = v['path_coords']
                    
        if best_global_path:
            consolidated_paths.extend([{"x": p[0], "z": p[1]} for p in best_global_path])
            
        # Envia para a UI apenas as zonas que estão no período de Cooldown (Perigo Ativo)
        lethal_zones = [{"x": p[0], "z": p[1]} for p in shared_knowledge.lethal_zones.keys() if shared_knowledge.is_dangerous(p[0], p[1])]

        return {
            "bestRoutes": [{"origin": f"X:{k[0]} Z:{k[1]}", "steps": v['steps'], "agent": v['agent_name'], "actions": v['actions'][:4] + ['...'] if len(v['actions'])>4 else v['actions']} for k, v in self.best_routes.items()],
            "leaderboard": [{"name": k, "successes": v['successes'], "bestTime": v['best_time']} for k, v in sorted(self.leaderboard.items(), key=lambda item: item[1]['successes'], reverse=True)[:5]],
            "stats": [{"origin": f"X:{k[0]} Z:{k[1]}", "attempts": v['attempts'], "successes": v['successes']} for k, v in self.origin_stats.items()],
            "consolidatedPaths": consolidated_paths,
            "lethalZones": lethal_zones
        }

# (O resto das classes no arquivo ai_navigation.py continua perfeitamente igual)
class EnvironmentSensor:
    @staticmethod
    def get_state(agent_pos, target_pos, shared_knowledge):
        dx = round((target_pos[0] - agent_pos[0]) / 2)
        dz = round((target_pos[1] - agent_pos[1]) / 2)
        
        return np.array([dx, dz])

class RewardSystem:
    @staticmethod
    def calculate(new_x, new_z, is_collision, is_out_of_bounds, hit_cactus, shared_knowledge, reached_target):
        if reached_target: return 500.0, True 
        if is_out_of_bounds: return -100.0, True
        if hit_cactus: return -100.0, True
        if shared_knowledge.is_dangerous(new_x, new_z): return -50.0, False 
        if is_collision: return -10.0, False
        return -1.0, False

class NeuralNetworkPlaceholder:
    def __init__(self):
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 1.0 
        self.epsilon_decay = 0.99
        
    def get_action(self, state):
        state_key = tuple(np.round(state, 1))
        if random.random() < self.epsilon:
            return random.randint(0, 3)
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0, 0.0, 0.0, 0.0]
        return np.argmax(self.q_table[state_key])
        
    def train(self, state, action, reward, next_state, done):
        state_key = tuple(np.round(state, 1))
        next_state_key = tuple(np.round(next_state, 1))
        if state_key not in self.q_table: self.q_table[state_key] = [0.0, 0.0, 0.0, 0.0]
        if next_state_key not in self.q_table: self.q_table[next_state_key] = [0.0, 0.0, 0.0, 0.0]
            
        best_next_action = np.max(self.q_table[next_state_key])
        current_q = self.q_table[state_key][action]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * best_next_action - current_q)
        self.q_table[state_key][action] = new_q
        if done: self.epsilon *= self.epsilon_decay

class AgentController:
    def __init__(self):
        self.brain = NeuralNetworkPlaceholder()
        self.shared_knowledge = SharedKnowledgeSystem()
        self.logger = EventLogSystem()
        self.analytics = RouteAnalyticsSystem(self.logger)
        
    def process_tick(self, agent_id, agent_pos, target_pos):
        self.shared_knowledge.tick() 
        
        state = EnvironmentSensor.get_state(agent_pos, target_pos, self.shared_knowledge)
        planned_action = self.analytics.get_planned_action(agent_id)
        
        if planned_action is not None:
            moves = [(0, -2), (0, 2), (-2, 0), (2, 0)] 
            dx, dz = moves[planned_action]
            next_x = agent_pos[0] + dx
            next_z = agent_pos[1] + dz
            
            if self.shared_knowledge.is_dangerous(next_x, next_z):
                self.analytics.abort_exploit(agent_id)
                action_idx = self.brain.get_action(state) 
            else:
                action_idx = planned_action
        else:
            action_idx = self.brain.get_action(state)
        
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0)] 
        dx, dz = moves[action_idx]
        next_x, next_z = agent_pos[0] + dx, agent_pos[1] + dz
        
        # BLINDAGEM INTELIGENTE
        if self.shared_knowledge.is_dangerous(next_x, next_z):
            safe_actions = []
            for i, (mx, mz) in enumerate(moves):
                if not self.shared_knowledge.is_dangerous(agent_pos[0] + mx, agent_pos[1] + mz):
                    safe_actions.append(i)
            
            if safe_actions:
                # O agente não entra mais em pânico aleatório! 
                # Ele pergunta à Rede Neural qual é o *melhor* caminho seguro.
                best_q = -float('inf')
                action_idx = safe_actions[0]
                state_key = tuple(np.round(state, 1))
                q_values = self.brain.q_table.get(state_key, [0.0, 0.0, 0.0, 0.0])
                
                for a in safe_actions:
                    if q_values[a] > best_q:
                        best_q = q_values[a]
                        action_idx = a
                        
                dx, dz = moves[action_idx]
        
        final_x = agent_pos[0] + dx
        final_z = agent_pos[1] + dz
        
        self.shared_knowledge.mark_safe(final_x, final_z)
        
        return final_x, final_z, int(action_idx), state