import math
import random

class FarmPlanner:
    def __init__(self):
        # O passo do nosso mundo é de 2 em 2 metros
        self.GRID_STEP = 2
        # As fronteiras deixam de estar fixas no __init__. 
        # Serão injetadas a cada tick pelo SurvivalController, que lê o Neo4j.

    # === ALTERAÇÃO 1: Novo parâmetro `world_bounds` injetado na raiz do planeamento ===
    def plan_new_farm(self, agent_pos, blocked_coords, crop_coords=None, restricted_plot_coords=None, world_bounds=None):
        if crop_coords is None:
            crop_coords = set()
        if restricted_plot_coords is None:
            restricted_plot_coords = set()
            
        # Extrai os limites dinâmicos da base de dados (com fallback seguro para -24/24)
        min_x = world_bounds['minX'] if world_bounds else -24
        max_x = world_bounds['maxX'] if world_bounds else 24
        min_z = world_bounds['minZ'] if world_bounds else -24
        max_z = world_bounds['maxZ'] if world_bounds else 24
            
        orientations = [(4, 6), (6, 4)]
        random.shuffle(orientations)
        
        search_radius = 16 
        
        for r in range(0, search_radius + 1, self.GRID_STEP):
            for dx in range(-r, r + 1, self.GRID_STEP):
                for dz in range(-r, r + 1, self.GRID_STEP):
                    # === CORREÇÃO CRÍTICA 1: Snap to Grid ===
                    start_x = round((agent_pos[0] + dx) / self.GRID_STEP) * self.GRID_STEP
                    start_z = round((agent_pos[1] + dz) / self.GRID_STEP) * self.GRID_STEP
                    
                    for width_nodes, height_nodes in orientations:
                        # === ALTERAÇÃO 2: Passamos os limites dinâmicos para a função de validação ===
                        if self._is_area_clear(int(start_x), int(start_z), width_nodes, height_nodes, blocked_coords, crop_coords, restricted_plot_coords, min_x, max_x, min_z, max_z):
                            return self._generate_plot_blueprint(int(start_x), int(start_z), width_nodes, height_nodes)
        return None

    # === ALTERAÇÃO 3: Aplicando a Lei de Zoneamento a um mapa em expansão ===
    def _is_area_clear(self, start_x, start_z, width_nodes, height_nodes, blocked_coords, crop_coords, restricted_plot_coords, min_x, max_x, min_z, max_z):
        plot_max_x = int(start_x + (width_nodes - 1) * self.GRID_STEP)
        plot_max_z = int(start_z + (height_nodes - 1) * self.GRID_STEP)
        
        # O limite geográfico deixou de ser 'self.MIN_COORD'
        if start_x < min_x or plot_max_x > max_x: return False
        if start_z < min_z or plot_max_z > max_z: return False
        
        for x in range(int(start_x), plot_max_x + 1, self.GRID_STEP):
            for z in range(int(start_z), plot_max_z + 1, self.GRID_STEP):
                # 1. Bateu numa parede, árvore ou limite da fazenda vizinha? Cancela.
                if (x, z) in blocked_coords:
                    return False
                
                # 2. NOVO: Bateu na MARGEM DE SEGURANÇA de outro terreno? Cancela.
                if (x, z) in restricted_plot_coords:
                    return False
                
                # 3. A REGRA DE OURO DA BATATA: A linha azul NUNCA pode esmagar uma planta!
                is_perimeter = (x == start_x or x == plot_max_x or z == start_z or z == plot_max_z)
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