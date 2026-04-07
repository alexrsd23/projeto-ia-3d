import math
import random
import numpy as np

class SharedKnowledgeSystem:
    def __init__(self):
        self.lethal_zones = set()

    def mark_danger(self, x, z):
        # Assegura precisão das coordenadas perigosas
        self.lethal_zones.add((float(x), float(z)))

    def is_dangerous(self, x, z):
        return (float(x), float(z)) in self.lethal_zones

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

# ==========================================
# EVOLUÇÃO: AMBIENTES DINÂMICOS E CONFIANÇA
# ==========================================
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
        
        # Dinamismo: Usa a confiança da rota para decidir se faz exploit
        if origin in self.best_routes:
            confidence = self.best_routes[origin].get('confidence', 0.85)
            if random.random() < confidence:
                mode = 'exploit'
                planned_route = self.best_routes[origin]['raw_actions']
            
        if agent_id not in self.active_episodes:
            self.active_episodes[agent_id] = {
                'origin': origin,
                'steps': 0,
                'actions': [],
                'raw_actions': [],
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
        """Força o agente a voltar a explorar se a rota estiver corrompida"""
        if agent_id in self.active_episodes:
            self.active_episodes[agent_id]['mode'] = 'explore'

    def record_step(self, agent_id, action_idx):
        if agent_id in self.active_episodes:
            actions_map = ["CIMA", "BAIXO", "ESQUERDA", "DIREITA"]
            self.active_episodes[agent_id]['steps'] += 1
            self.active_episodes[agent_id]['actions'].append(actions_map[action_idx])
            self.active_episodes[agent_id]['raw_actions'].append(int(action_idx))

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
            
            # Se encontrou uma rota melhor (ou a primeira)
            if origin not in self.best_routes or score < self.best_routes[origin]['score']:
                self.best_routes[origin] = {
                    'score': score,
                    'steps': ep['steps'],
                    'agent_name': agent_name,
                    'actions': ep['actions'],
                    'raw_actions': ep['raw_actions'],
                    'confidence': 0.85, # Alta confiança inicial
                    'fails': 0
                }
            else:
                # Se fez a mesma rota com sucesso, consolida a confiança
                if self.best_routes[origin]['raw_actions'] == ep['raw_actions']:
                    self.best_routes[origin]['confidence'] = min(0.95, self.best_routes[origin].get('confidence', 0.85) + 0.05)
                    self.best_routes[origin]['fails'] = 0
        else:
            # PENALIZAÇÃO E INVALIDAÇÃO DE ROTA (Ambiente Dinâmico)
            if ep['mode'] == 'exploit' and origin in self.best_routes:
                self.best_routes[origin]['fails'] = self.best_routes[origin].get('fails', 0) + 1
                
                # A confiança despenca com cada morte (menos agentes vão tentar)
                self.best_routes[origin]['confidence'] = max(0.10, self.best_routes[origin].get('confidence', 0.85) - 0.25)
                
                # Após 3 mortes na mesma rota "perfeita", assume-se que o ambiente mudou
                if self.best_routes[origin]['fails'] >= 3:
                    self.logger.log("WARNING", f"🔄 Rota de X:{origin[0]} Z:{origin[1]} INVALIDADA por bloqueios! Área entrou em Reexploração.")
                    del self.best_routes[origin] # Apaga a rota da memória

        del self.active_episodes[agent_id]

    def get_telemetry_data(self):
        return {
            "bestRoutes": [{"origin": f"X:{k[0]} Z:{k[1]}", "steps": v['steps'], "agent": v['agent_name'], "actions": v['actions'][:4] + ['...'] if len(v['actions'])>4 else v['actions']} for k, v in self.best_routes.items()],
            "leaderboard": [{"name": k, "successes": v['successes'], "bestTime": v['best_time']} for k, v in sorted(self.leaderboard.items(), key=lambda item: item[1]['successes'], reverse=True)[:5]],
            "stats": [{"origin": f"X:{k[0]} Z:{k[1]}", "attempts": v['attempts'], "successes": v['successes']} for k, v in self.origin_stats.items()]
        }

class EnvironmentSensor:
    @staticmethod
    def get_state(agent_pos, target_pos, shared_knowledge):
        ax, az = agent_pos
        tx, tz = target_pos
        dist_x = tx - ax
        dist_z = tz - az
        norm = math.hypot(dist_x, dist_z)
        dir_x = dist_x / norm if norm > 0 else 0
        dir_z = dist_z / norm if norm > 0 else 0
        return np.array([dir_x, dir_z])

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
        # O Logger agora é passado para o Analytics reportar a Invalidação de Rotas
        self.analytics = RouteAnalyticsSystem(self.logger)
        
    def process_tick(self, agent_id, agent_pos, target_pos):
        state = EnvironmentSensor.get_state(agent_pos, target_pos, self.shared_knowledge)
        
        planned_action = self.analytics.get_planned_action(agent_id)
        
        if planned_action is not None:
            # O "SENTIDO-ARANHA": Olha para onde vai pisar ANTES de o fazer
            moves = [(0, -2), (0, 2), (-2, 0), (2, 0)] 
            dx, dz = moves[planned_action]
            next_x = agent_pos[0] + dx
            next_z = agent_pos[1] + dz
            
            # Se alguém morreu ali antes (Conhecimento Compartilhado), aborta o Exploit!
            if self.shared_knowledge.is_dangerous(next_x, next_z):
                self.analytics.abort_exploit(agent_id)
                action_idx = self.brain.get_action(state) # Força improvisação
            else:
                action_idx = planned_action
        else:
            action_idx = self.brain.get_action(state)
        
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0)] 
        dx, dz = moves[action_idx]
        
        return agent_pos[0] + dx, agent_pos[1] + dz, int(action_idx), state