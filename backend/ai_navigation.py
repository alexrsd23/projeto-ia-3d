import math
import random
import numpy as np

class SharedKnowledgeSystem:
    """Memória global do ambiente compartilhada entre todos os agentes"""
    def __init__(self):
        self.lethal_zones = set() # Conjunto de coordenadas perigosas (x, z)

    def mark_danger(self, x, z):
        self.lethal_zones.add((x, z))

    def is_dangerous(self, x, z):
        return (x, z) in self.lethal_zones

class EventLogSystem:
    """Captura e estrutura eventos da simulação para enviar ao Frontend"""
    def __init__(self):
        self.events = []
        self.counter = 0

    def log(self, level, message):
        self.counter += 1
        self.events.append({
            "id": f"evt-{self.counter}",
            "level": level,
            "message": message,
            "timestamp": "now" # O React tratará o tempo visual
        })

    def flush(self):
        """Retorna os eventos atuais e limpa a fila"""
        res = self.events.copy()
        self.events.clear()
        return res

class EnvironmentSensor:
    @staticmethod
    def get_state(agent_pos, target_pos, shared_knowledge):
        ax, az = agent_pos
        tx, tz = target_pos
        
        # O agente agora "sente" a direção do objetivo
        dist_x = tx - ax
        dist_z = tz - az
        norm = math.hypot(dist_x, dist_z)
        dir_x = dist_x / norm if norm > 0 else 0
        dir_z = dist_z / norm if norm > 0 else 0
        
        return np.array([dir_x, dir_z])

class RewardSystem:
    @staticmethod
    def calculate(new_x, new_z, is_collision, is_out_of_bounds, hit_cactus, shared_knowledge, reached_target):
        # 1. Sucesso Absoluto (Caminho concluído)
        if reached_target:
            return 500.0, True 
            
        # 2. Falhas Críticas (Letais)
        if is_out_of_bounds:
            return -100.0, True
        if hit_cactus:
            return -100.0, True
            
        # 3. Penalidades Ambientais
        if shared_knowledge.is_dangerous(new_x, new_z):
            return -50.0, False # Penalidade severa por ignorar a memória global
        if is_collision:
            return -10.0, False
            
        # 4. Custo por passo padrão (incentiva o caminho mais curto)
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
            return random.randint(0, 3) # 0: Cima, 1: Baixo, 2: Esq, 3: Dir
            
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0, 0.0, 0.0, 0.0]
        return np.argmax(self.q_table[state_key])
        
    def train(self, state, action, reward, next_state, done):
        state_key = tuple(np.round(state, 1))
        next_state_key = tuple(np.round(next_state, 1))
        
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0, 0.0, 0.0, 0.0]
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = [0.0, 0.0, 0.0, 0.0]
            
        best_next_action = np.max(self.q_table[next_state_key])
        current_q = self.q_table[state_key][action]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * best_next_action - current_q)
        self.q_table[state_key][action] = new_q
        
        if done:
            self.epsilon *= self.epsilon_decay

class AgentController:
    def __init__(self):
        self.brain = NeuralNetworkPlaceholder()
        self.shared_knowledge = SharedKnowledgeSystem()
        self.logger = EventLogSystem()
        
    def process_tick(self, agent_pos, target_pos):
        state = EnvironmentSensor.get_state(agent_pos, target_pos, self.shared_knowledge)
        action_idx = self.brain.get_action(state)
        
        # Movimentação Restrita a células adjacentes exatas (salto de 2 metros = 1 célula)
        moves = [(0, -2), (0, 2), (-2, 0), (2, 0)] # Cima, Baixo, Esq, Dir
        dx, dz = moves[action_idx]
        
        return agent_pos[0] + dx, agent_pos[1] + dz, int(action_idx), state