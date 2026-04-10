import random
import uuid

class ForestrySystem:
    @staticmethod
    def process_chopping(tree_entity, current_time, agent_name):
        """
        Processa o corte: Transforma a árvore num toco e gera 3 troncos físicos ao redor.
        """
        # 1. A árvore original transforma-se num Toco (Mantém o ID original)
        stump_update = {
            "id": tree_entity['id'], 
            "type": "stump", 
            "x": tree_entity['x'], 
            "z": tree_entity['z'], 
            "hp": 0, "hunger": 0, "inv": "{}", "mem": "{}", "state": "IDLE"
        }

        # 2. Gerar 3 troncos (logs) espalhados ao redor da árvore
        new_logs = []
        # Possíveis posições adjacentes na nossa grade 2x2
        offsets = [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)]
        chosen_offsets = random.sample(offsets, 3)

        for offset in chosen_offsets:
            # Trava matemática para o tronco não cair fora do mundo
            log_x = max(-24, min(24, tree_entity['x'] + offset[0]))
            log_z = max(-24, min(24, tree_entity['z'] + offset[1]))
            
            new_logs.append({
                "id": str(uuid.uuid4()),
                "type": "log",
                "posX": log_x,
                "posY": -0.35, # A gravidade exata para ele ficar deitado no chão
                "posZ": log_z,
                "health": 0, "hunger": 0, "name": "Tronco Caído",
                "inventoryJSON": "{}", "memoryJSON": "{}", "state": "IDLE"
            })

        event = {
            "id": str(uuid.uuid4()), 
            "level": "SUCCESS", 
            "message": f"🪓 {agent_name} derrubou uma árvore! 3 troncos caíram no chão.", 
            "timestamp": current_time
        }
        
        return stump_update, new_logs, event