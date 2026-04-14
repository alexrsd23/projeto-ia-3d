import math
import random

class FarmPlanner:
    def __init__(self):
        # O passo do nosso mundo é de 2 em 2 metros
        self.GRID_STEP = 2
        # Limites do mapa atual
        self.MIN_COORD = -24
        self.MAX_COORD = 24

    def plan_new_farm(self, agent_pos, blocked_coords):
        """
        Função Principal: O Fazendeiro chama esta função quando quer criar uma fazenda.
        Ela faz uma varredura em espiral ao redor do fazendeiro procurando um terreno 4x6 ou 6x4.
        Retorna o dicionário "Blueprint" se encontrar espaço, ou None se o mapa estiver lotado.
        """
        # Define as duas orientações possíveis (Horizontal e Vertical)
        orientations = [(4, 6), (6, 4)]
        random.shuffle(orientations)
        
        # Faz uma busca em espiral (busca primeiro perto, depois vai alargando)
        search_radius = 16 # Busca num raio de até 16 blocos
        
        for r in range(0, search_radius + 1, self.GRID_STEP):
            for dx in range(-r, r + 1, self.GRID_STEP):
                for dz in range(-r, r + 1, self.GRID_STEP):
                    # Testa o ponto inicial (canto superior esquerdo do lote)
                    start_x = agent_pos[0] + dx
                    start_z = agent_pos[1] + dz
                    
                    for width_nodes, height_nodes in orientations:
                        if self._is_area_clear(start_x, start_z, width_nodes, height_nodes, blocked_coords):
                            # Se a área está livre, gera a planta da fazenda!
                            return self._generate_plot_blueprint(start_x, start_z, width_nodes, height_nodes)
                            
        return None # Não há espaço suficiente por perto

    def _is_area_clear(self, start_x, start_z, width_nodes, height_nodes, blocked_coords):
        """
        Sub-função de Validação:
        Verifica se o retângulo inteiro (incluindo o interior) não ultrapassa as bordas do mundo
        e não colide com árvores, cactos ou cercas de outras pessoas.
        """
        max_x = start_x + (width_nodes - 1) * self.GRID_STEP
        max_z = start_z + (height_nodes - 1) * self.GRID_STEP
        
        # 1. Verifica os limites do mundo (não pode construir fora da malha)
        if start_x < self.MIN_COORD or max_x > self.MAX_COORD: return False
        if start_z < self.MIN_COORD or max_z > self.MAX_COORD: return False
        
        # 2. Verifica todos os nós dentro dessa área
        for x in range(start_x, max_x + 1, self.GRID_STEP):
            for z in range(start_z, max_z + 1, self.GRID_STEP):
                # Se QUALQUER ponto dentro do 4x6 tiver um obstáculo, o terreno é rejeitado
                if (x, z) in blocked_coords:
                    return False
                    
        return True

    def _generate_plot_blueprint(self, start_x, start_z, width_nodes, height_nodes):
        """
        Sub-função Arquiteta:
        Separa matematicamente o perímetro do interior e formata para o Banco de Dados.
        """
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
        
        # === A ALTERAÇÃO ESTÁ AQUI: Formato compatível com o PlotModel ===
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