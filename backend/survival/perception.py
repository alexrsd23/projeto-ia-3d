import math
import json

# =====================================================================
# SISTEMA DE PERCEPÇÃO: O Radar de Curto Alcance do Agente
# =====================================================================

class PerceptionSystem:
    def __init__(self, vision_radius=15.0):
        # Quantos blocos de distância o agente consegue ver
        self.vision_radius = vision_radius

    def scan_environment(self, agent_pos, world_entities, world_tiles, peer_agents=[]):
        """
        Filtra o mundo global e devolve apenas o que o agente consegue ver,
        já organizado e ordenado do mais próximo para o mais distante.
        """
        ax, az = agent_pos[0], agent_pos[1]
        
        seen_data = {
            "food_ready": [],      # Batatas prontas a colher (Estágio 2)
            "food_growing": [],    # Batatas a crescer (Estágio 0 e 1)
            "hazards": [],         # Obstáculos perigosos (Cactos)
            "arable_land": [],     # Grama selvagem (boa para arar)
            "empty_farms": [],     # Terra arada (boa para plantar)
            "other_agents": []     # Concorrência / Outros agentes
        }

        # 1. Analisa as Entidades Físicas (Cactos, Árvores, Loot, etc)
        for entity in world_entities:
            ex, ez = entity.get('x'), entity.get('z')
            if ex is None or ez is None:
                continue
                
            dist = math.hypot(ex - ax, ez - az)
            
            # === A CORREÇÃO ESTÁ AQUI: Removemos o "0.1 <" ===
            if dist <= self.vision_radius:
                item = {"id": entity['id'], "x": ex, "z": ez, "dist": dist}
                
                if entity['type'] == 'cactus':
                    seen_data["hazards"].append(item)
                elif entity['type'] == 'character':
                    seen_data["other_agents"].append(item)
                elif entity['type'] == 'loot':
                    seen_data.setdefault("loots", []).append(item)
                elif entity['type'] == 'tree':
                    seen_data.setdefault("trees", []).append(item)
                elif entity['type'] == 'damaged_fence':
                    seen_data.setdefault("broken_fences", []).append(item)
                elif entity['type'] == 'log':
                    seen_data.setdefault("logs_on_ground", []).append(item)
                elif entity['type'] in ['fence', 'gate']:
                    seen_data.setdefault("fences", []).append(item)

        # 2. Analisa o Chão e as Plantações (Tiles)
        for tile in world_tiles:
            tx, tz = tile.get('x'), tile.get('z')
            if tx is None or tz is None:
                continue
                
            dist = math.hypot(tx - ax, tz - az)
            
            if dist <= self.vision_radius:
                if tile['type'] == 'grass':
                    seen_data["arable_land"].append({"id": tile['id'], "x": tx, "z": tz, "dist": dist})
                
                elif tile['type'] == 'farm':
                    raw_crops = tile.get('cropsJSON')
                    crops = []
                    if raw_crops:
                        try:
                            crops = json.loads(raw_crops)
                        except:
                            pass

                    # NOVO: Uma terra é um alvo válido para plantar se tiver 0 ou 1 planta!
                    if len(crops) < 2:
                        seen_data["empty_farms"].append({"id": tile['id'], "x": tx, "z": tz, "dist": dist})
                    
                    # Continua a processar as plantas que lá estão para ver se estão maduras
                    for crop in crops:
                        crop_info = {
                            "id": crop['id'], 
                            "tile_id": tile['id'],
                            "x": tx, "z": tz, 
                            "stage": crop['stage'], 
                            "dist": dist
                        }
                        if crop['stage'] == 2:
                            seen_data["food_ready"].append(crop_info)
                        else:
                            seen_data["food_growing"].append(crop_info)

        # 3. Otimização: Ordena tudo do mais perto para o mais longe
        # Isto facilita o trabalho do cérebro para ir sempre à batata mais próxima
        for key in seen_data:
            seen_data[key] = sorted(seen_data[key], key=lambda item: item['dist'])

        # === NOVO: O RADAR SOCIAL (Vê os outros bonecos) ===
        for peer in peer_agents:
            px, pz = peer.get('x'), peer.get('z')
            if px is None or pz is None or peer.get('id') == agent_pos[2]: # Passaremos o agent_id na pos[2] para ele não ver a si mesmo
                continue
                
            dist = math.hypot(px - ax, pz - az)
            if dist <= self.vision_radius:
                seen_data["other_agents"].append({
                    "id": peer['id'], 
                    "type": peer['type'], 
                    "name": peer.get('name', 'Desconhecido'),
                    "sex": peer.get('sex', 'M'),           # <--- ADICIONAR ISTO
                    "married": peer.get('married', False), # <--- ADICIONAR ISTO
                    "x": px, "z": pz, 
                    "dist": dist
                })

        # 3. Otimização: Ordena tudo do mais perto para o mais longe
        for key in seen_data:
            seen_data[key] = sorted(seen_data[key], key=lambda item: item['dist'])

        return seen_data