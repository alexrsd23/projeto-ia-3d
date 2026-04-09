import math

# =====================================================================
# SISTEMA DE MEMÓRIA: O Hipocampo e a Memória Espacial do Agente
# =====================================================================

class SpatialMemory:
    def __init__(self):
        # Estrutura: { agent_id: { 'food': {}, 'farms': {}, 'hazards': {} } }
        self.agent_memories = {}

    def _ensure_agent(self, agent_id):
        """Garante que o agente tem um cérebro alocado para memórias."""
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = {
                'food': {},      # Dicionário de coordenadas com batatas (prontas ou a crescer)
                'farms': {},     # Dicionário de terras aráveis ou fazendas vazias
                'hazards': {}    # Locais a evitar (cactos, etc.)
            }

    def update_from_perception(self, agent_id, radar_data, current_tick):
        """
        Pega no que o Radar viu neste exato momento e grava/atualiza na memória.
        A fiabilidade é restaurada para 1.0 (100% de certeza porque acabou de ver).
        """
        self._ensure_agent(agent_id)
        memory = self.agent_memories[agent_id]

        # 1. Memorizar Comida (Pronta ou a Crescer)
        all_food_seen = radar_data.get('food_ready', []) + radar_data.get('food_growing', [])
        for item in all_food_seen:
            coord = (item['x'], item['z'])
            memory['food'][coord] = {
                'stage': item['stage'],
                'reliability': 1.0,       # Tenho a certeza absoluta, estou a ver agora
                'last_seen': current_tick
            }

        # 2. Memorizar Terras Aráveis (Para quando precisar de ser agricultor)
        all_farms_seen = radar_data.get('empty_farms', []) + radar_data.get('arable_land', [])
        for item in all_farms_seen:
            coord = (item['x'], item['z'])
            memory['farms'][coord] = {
                'type': 'empty_farm' if 'empty_farms' in str(item) else 'grass',
                'reliability': 1.0,
                'last_seen': current_tick
            }

        # 3. Memorizar Perigos
        for item in radar_data.get('hazards', []):
            coord = (item['x'], item['z'])
            memory['hazards'][coord] = {
                'reliability': 1.0,
                'last_seen': current_tick
            }

    def invalidate_food_memory(self, agent_id, coord):
        """
        O momento da deceção: O agente chegou ao local onde se lembrava de haver
        comida, mas outro agente já a comeu. Apagamos a memória.
        """
        self._ensure_agent(agent_id)
        if coord in self.agent_memories[agent_id]['food']:
            del self.agent_memories[agent_id]['food'][coord]
            # Nota: Poderíamos apenas reduzir a fiabilidade (ex: 0.5), mas para comida
            # se não está lá, é porque desapareceu fisicamente.
            
    def invalidate_farm_memory(self, agent_id, coord):
        """
        O momento da desassociação: O agente chegou na terra para plantar, 
        mas descobriu que ela já está lotada de sementes. Apagamos a memória
        para ele parar de fazer acampamento e ir procurar outro terreno.
        """
        self._ensure_agent(agent_id)
        if coord in self.agent_memories[agent_id]['farms']:
            del self.agent_memories[agent_id]['farms'][coord]

    def get_best_food_source(self, agent_id, current_pos):
        self._ensure_agent(agent_id)
        food_memories = self.agent_memories[agent_id]['food']

        best_coord = None
        best_score = -float('inf')

        for coord, data in food_memories.items():
            # NOVO: O FIM DO CAMPING! Se a planta não estiver no estágio 2, 
            # ele não considera andar até lá para buscar comida.
            if data['stage'] < 2:
                continue 
                
            dist = math.hypot(coord[0] - current_pos[0], coord[1] - current_pos[1])
            if dist == 0: 
                dist = 0.1 

            score = data['reliability'] / dist

            if score > best_score:
                best_score = score
                best_coord = coord

        return best_coord

    def get_best_farm_location(self, agent_id, current_pos):
        """
        Quando o instinto agricultor bate, ele procura o melhor local para plantar.
        Prefere fazendas já aradas (empty_farms) em vez de grama bruta.
        """
        self._ensure_agent(agent_id)
        farm_memories = self.agent_memories[agent_id]['farms']
        
        best_coord = None
        best_score = -float('inf')
        
        for coord, data in farm_memories.items():
            dist = math.hypot(coord[0] - current_pos[0], coord[1] - current_pos[1])
            if dist == 0: dist = 0.1
            
            # Prefere uma terra que já foi arada no passado
            type_multiplier = 2.0 if data['type'] == 'empty_farm' else 1.0
            
            score = (data['reliability'] * type_multiplier) / dist
            
            if score > best_score:
                best_score = score
                best_coord = coord
                
        return best_coord