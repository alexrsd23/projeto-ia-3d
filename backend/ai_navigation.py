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
        self.spawn_counters = {}
        self.subpath_suggestions = {}

    def start_episode(self, agent_id, origin_x, origin_z):
        origin = (float(origin_x), float(origin_z))
        is_new = False
        
        if agent_id not in self.active_episodes:
            is_new = True
            mode = 'explore'
            planned_route = []
            
            if origin in self.best_routes:
                plateau = self.best_routes[origin].get('plateau', 0)
                
                # Regista mais um nascimento nesta coordenada exata
                self.spawn_counters[origin] = self.spawn_counters.get(origin, 0) + 1
                spawn_count = self.spawn_counters[origin]
                
                # A SUA REGRA DETERMINÍSTICA: Fim das probabilidades aleatórias!
                if plateau < 25:
                    # FASE DE APRENDIZADO: A cada 4 nascimentos, 1 é explorador (3 Azuis, 1 Vermelho)
                    # Se o resto da divisão por 4 não for zero, ele é Seguidor (Exploit).
                    if spawn_count % 4 != 0:
                        mode = 'exploit'
                else:
                    # FASE DO CAMINHO PERFEITO: A cada 11 nascimentos, 1 é explorador (10 Azuis, 1 Vermelho)
                    if spawn_count % 11 != 0:
                        mode = 'exploit'
                
                if mode == 'exploit':
                    planned_route = self.best_routes[origin]['raw_actions']
            
            self.active_episodes[agent_id] = {
                'origin': origin,
                'steps': 0,
                'actions': [],
                'raw_actions': [],
                'path_coords': [origin],
                'mode': mode,
                'original_mode': mode,
                'planned_route': planned_route
            }
            
        return self.active_episodes[agent_id]['mode'], is_new

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
            # Expandido para 8 direções
            actions_map = ["CIMA", "BAIXO", "ESQUERDA", "DIREITA", "DIAG_CE", "DIAG_CD", "DIAG_BE", "DIAG_BD"]
            self.active_episodes[agent_id]['steps'] += 1
            self.active_episodes[agent_id]['actions'].append(actions_map[action_idx])
            self.active_episodes[agent_id]['raw_actions'].append(int(action_idx))
            self.active_episodes[agent_id]['path_coords'].append((float(new_x), float(new_z)))

    def finalize_episode(self, agent_id, success, agent_name):
        if agent_id not in self.active_episodes:
            return
        
        ep = self.active_episodes[agent_id]
        origin = ep['origin']
        
        shortcut_found = False
        
        # =================================================================
        # NOVA REGRA: OTIMIZAÇÃO POR CONSENSO (Swarm Intelligence)
        # =================================================================
        if origin in self.best_routes and ep['original_mode'] == 'explore':
            old_path = self.best_routes[origin]['path_coords']
            old_raw = self.best_routes[origin]['raw_actions']
            old_str = self.best_routes[origin]['actions']
            
            if origin not in self.subpath_suggestions:
                self.subpath_suggestions[origin] = {}
            
            # Analisa cada passo dado pelo explorador (Gera a evolução hierárquica naturalmente)
            for idx_new, coord in enumerate(ep['path_coords']):
                if coord in old_path:
                    idx_old = old_path.index(coord)
                    # Se ele chegou à mesma coordenada usando MENOS passos, é um atalho!
                    if idx_new < idx_old:
                        # Em vez de aplicar logo, cria uma "Assinatura/Hash" deste atalho exato
                        shortcut_hash = tuple(ep['path_coords'][:idx_new+1])
                        
                        if shortcut_hash not in self.subpath_suggestions[origin]:
                            self.subpath_suggestions[origin][shortcut_hash] = {
                                'votes': 1,
                                'path': ep['path_coords'][:idx_new+1],
                                'raw': ep['raw_actions'][:idx_new],
                                'str': ep['actions'][:idx_new],
                                'idx_old': idx_old
                            }
                        else:
                            # Replicação independente confirmada! Aumenta o voto.
                            self.subpath_suggestions[origin][shortcut_hash]['votes'] += 1
                            
                        votes = self.subpath_suggestions[origin][shortcut_hash]['votes']
                        
                        # CONSENSO: Precisamos de 5 votos idênticos para aprovar 
                        # (Usei 5 para manter a simulação fluída, mas a lógica é a que propôs)
                        if votes >= 5:
                            stitched_path = self.subpath_suggestions[origin][shortcut_hash]['path'] + old_path[idx_old+1:]
                            stitched_raw = self.subpath_suggestions[origin][shortcut_hash]['raw'] + old_raw[idx_old:]
                            stitched_str = self.subpath_suggestions[origin][shortcut_hash]['str'] + old_str[idx_old:]
                            
                            self.best_routes[origin]['path_coords'] = stitched_path
                            self.best_routes[origin]['raw_actions'] = stitched_raw
                            self.best_routes[origin]['actions'] = stitched_str
                            self.best_routes[origin]['steps'] = len(stitched_raw)
                            self.best_routes[origin]['score'] = len(stitched_raw)
                            self.best_routes[origin]['plateau'] = 0 
                            self.best_routes[origin]['fails'] = 0
                            
                            steps_saved = idx_old - idx_new
                            self.logger.log("SUCCESS", f"✅ Consenso Atingido! Atalho validado na rota X:{origin[0]} Z:{origin[1]} (-{steps_saved} passos).")
                            
                            # Limpa a urna de votação pois a rota base mudou e novos atalhos precisam ser achados
                            self.subpath_suggestions[origin] = {}
                        
                        shortcut_found = True
                        break # O explorador fez a sua parte, sai do loop
        
        if origin not in self.origin_stats:
            self.origin_stats[origin] = {'attempts': 0, 'successes': 0}
            
        self.origin_stats[origin]['attempts'] += 1
        
        if success:
            self.origin_stats[origin]['successes'] += 1
            
            if agent_name not in self.leaderboard:
                self.leaderboard[agent_name] = {'successes': 0, 'best_time': 9999}
            
            self.leaderboard[agent_name]['successes'] += 1
            self.leaderboard[agent_name]['best_time'] = min(
                self.leaderboard[agent_name]['best_time'], ep['steps']
            )
            
            score = ep['steps']
            final_pos = ep['path_coords'][-1]
            math_min_steps = math.ceil(max(abs(final_pos[0] - origin[0]) / 2, abs(final_pos[1] - origin[1]) / 2))
            is_perfect_route = (score <= math_min_steps + 1)
            
            if origin not in self.best_routes or score < self.best_routes[origin]['score']:
                self.best_routes[origin] = {
                    'score': score,
                    'steps': ep['steps'],
                    'agent_name': agent_name,
                    'actions': ep['actions'],
                    'raw_actions': ep['raw_actions'],
                    'path_coords': ep['path_coords'],
                    'fails': 0,
                    'plateau': 999 if is_perfect_route else 0
                }
                
                if is_perfect_route:
                    self.logger.log("SUCCESS", f"⭐ Rota Perfeita Matematicamente encontrada para a origem X:{origin[0]} Z:{origin[1]}!")
            else:
                if ep['original_mode'] == 'explore':
                    if not shortcut_found:
                        if self.best_routes[origin].get('plateau', 0) < 999:
                            self.best_routes[origin]['plateau'] = self.best_routes[origin].get('plateau', 0) + 1
                    
                    if is_perfect_route:
                         self.best_routes[origin]['plateau'] = 999
                
                if self.best_routes[origin]['raw_actions'] == ep['raw_actions']:
                    self.best_routes[origin]['fails'] = 0
                    
        else:
            if origin in self.best_routes:
                if ep['original_mode'] == 'exploit':
                    self.best_routes[origin]['fails'] = self.best_routes[origin].get('fails', 0) + 1
                    
                    tolerance = 10 if self.best_routes[origin].get('plateau', 0) >= 999 else 2
                    
                    if self.best_routes[origin]['fails'] >= tolerance:
                        self.logger.log(
                            "WARNING",
                            f"🔄 Rota de X:{origin[0]} Z:{origin[1]} INVALIDADA (Falhas excessivas)."
                        )
                        del self.best_routes[origin]
                
                elif ep['original_mode'] == 'explore':
                    if not shortcut_found:
                        if self.best_routes[origin].get('plateau', 0) < 999:
                            self.best_routes[origin]['plateau'] = self.best_routes[origin].get('plateau', 0) + 1

        del self.active_episodes[agent_id]

    def get_telemetry_data(self, shared_knowledge):
        consolidated_paths = []
        
        # CORREÇÃO VISUAL: Em vez de desenhar só a melhor rota do mundo, 
        # desenha a melhor rota DE CADA ORIGEM (nascimento) registada no banco!
        for k, v in self.best_routes.items():
            consolidated_paths.extend([{"x": p[0], "z": p[1]} for p in v['path_coords']])
            
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
            return random.randint(0, 7) # Agora a IA tem 8 ações (0 a 7)
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0] * 8 # O cérebro nasce com 8 neurônios de saída
        return np.argmax(self.q_table[state_key])
        
    def train(self, state, action, reward, next_state, done):
        state_key = tuple(np.round(state, 1))
        next_state_key = tuple(np.round(next_state, 1))
        
        if state_key not in self.q_table: self.q_table[state_key] = [0.0] * 8
        if next_state_key not in self.q_table: self.q_table[next_state_key] = [0.0] * 8
            
        best_next_action = np.max(self.q_table[next_state_key])
        current_q = self.q_table[state_key][action]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * best_next_action - current_q)
        self.q_table[state_key][action] = new_q
        
        if done: self.epsilon = max(0.20, self.epsilon * self.epsilon_decay)

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
        
        # AS 8 DIREÇÕES (Movimento em Vizinhança de Moore)
        moves = [
            (0, -2), (0, 2), (-2, 0), (2, 0),    # Ortogonais: Cima, Baixo, Esq, Dir
            (-2, -2), (2, -2), (-2, 2), (2, 2)   # Diagonais
        ]
        
        if planned_action is not None:
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
        
        dx, dz = moves[action_idx]
        next_x, next_z = agent_pos[0] + dx, agent_pos[1] + dz
        
        # BLINDAGEM INTELIGENTE
        if self.shared_knowledge.is_dangerous(next_x, next_z):
            safe_actions = []
            for i, (mx, mz) in enumerate(moves):
                if not self.shared_knowledge.is_dangerous(agent_pos[0] + mx, agent_pos[1] + mz):
                    safe_actions.append(i)
            
            if safe_actions:
                best_q = -float('inf')
                action_idx = safe_actions[0]
                state_key = tuple(np.round(state, 1))
                q_values = self.brain.q_table.get(state_key, [0.0] * 8)
                
                for a in safe_actions:
                    if q_values[a] > best_q:
                        best_q = q_values[a]
                        action_idx = a
                        
                dx, dz = moves[action_idx]
        
        final_x = agent_pos[0] + dx
        final_z = agent_pos[1] + dz
        
        self.shared_knowledge.mark_safe(final_x, final_z)
        
        return final_x, final_z, int(action_idx), state