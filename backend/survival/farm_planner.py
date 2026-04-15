import math
import random

class FarmPlanner:
    def __init__(self):
        # O passo do nosso mundo é de 2 em 2 metros
        self.GRID_STEP = 2
        # Limites do mapa atual
        self.MIN_COORD = -24
        self.MAX_COORD = 24

    # === ALTERAÇÃO 1: Adicionado o parâmetro restricted_plot_coords ===
    def plan_new_farm(self, agent_pos, blocked_coords, crop_coords=None, restricted_plot_coords=None):
        if crop_coords is None:
            crop_coords = set()
        if restricted_plot_coords is None:
            restricted_plot_coords = set()
            
        orientations = [(4, 6), (6, 4)]
        random.shuffle(orientations)
        
        search_radius = 16 
        
        for r in range(0, search_radius + 1, self.GRID_STEP):
            for dx in range(-r, r + 1, self.GRID_STEP):
                for dz in range(-r, r + 1, self.GRID_STEP):
                    # === CORREÇÃO CRÍTICA 1: Snap to Grid ===
                    # Força o número a ser arredondado para o múltiplo de GRID_STEP (2) mais próximo.
                    # Garante que as bordas nunca fiquem em coordenadas ímpares desalinhadas.
                    start_x = round((agent_pos[0] + dx) / self.GRID_STEP) * self.GRID_STEP
                    start_z = round((agent_pos[1] + dz) / self.GRID_STEP) * self.GRID_STEP
                    
                    for width_nodes, height_nodes in orientations:
                        if self._is_area_clear(int(start_x), int(start_z), width_nodes, height_nodes, blocked_coords, crop_coords, restricted_plot_coords):
                            return self._generate_plot_blueprint(int(start_x), int(start_z), width_nodes, height_nodes)
        return None

    # === ALTERAÇÃO 2: Aplicando a Lei de Zoneamento ===
    def _is_area_clear(self, start_x, start_z, width_nodes, height_nodes, blocked_coords, crop_coords, restricted_plot_coords):
        max_x = int(start_x + (width_nodes - 1) * self.GRID_STEP)
        max_z = int(start_z + (height_nodes - 1) * self.GRID_STEP)
        
        if start_x < self.MIN_COORD or max_x > self.MAX_COORD: return False
        if start_z < self.MIN_COORD or max_z > self.MAX_COORD: return False
        
        for x in range(int(start_x), max_x + 1, self.GRID_STEP):
            for z in range(int(start_z), max_z + 1, self.GRID_STEP):
                # 1. Bateu numa parede, árvore ou limite da fazenda vizinha? Cancela.
                if (x, z) in blocked_coords:
                    return False
                
                # 2. NOVO: Bateu na MARGEM DE SEGURANÇA de outro terreno? Cancela.
                if (x, z) in restricted_plot_coords:
                    return False
                
                # 3. A REGRA DE OURO DA BATATA: A linha azul NUNCA pode esmagar uma planta!
                is_perimeter = (x == start_x or x == max_x or z == start_z or z == max_z)
                if is_perimeter and (x, z) in crop_coords:
                    return False
                    
        return True

    def _generate_plot_blueprint(self, start_x, start_z, width_nodes, height_nodes):
        max_x = start_x + (width_nodes - 1) * self.GRID_STEP
        max_z = start_z + (height_nodes - 1) * self.GRID_STEP
        
        perimeter_nodes = []
        interior_nodes = []
        
        for x in range(start_x, max_x + 1, self.GRID_STEP):
            for z in range(start_z, max_z + 1, self.GRID_STEP):
                is_perimeter = (x == start_x or x == max_x or z == start_z or z == max_z)
                if is_perimeter:
                    perimeter_nodes.append((x, z))
                else:
                    interior_nodes.append((x, z))
                    
        corners = [(start_x, start_z), (start_x, max_z), (max_x, start_z), (max_x, max_z)]
        valid_gate_spots = [p for p in perimeter_nodes if p not in corners]
        gate_pos = random.choice(valid_gate_spots)
        
        fences_pos = [p for p in perimeter_nodes if p != gate_pos]
        
        return {
            "startX": start_x,
            "startZ": start_z,
            "width": width_nodes,
            "height": height_nodes,
            "status": "planned",
            "gate": gate_pos,
            "fences": fences_pos,
            "arable_lands": interior_nodes
        }