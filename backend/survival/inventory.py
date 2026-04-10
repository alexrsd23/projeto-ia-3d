import json

class InventorySystem:
    def __init__(self):
        # Limites de Estoque
        self.MAX_POTATOES = 4
        self.MAX_SEEDS = 4
        self.MAX_LOGS = 10     # Limite do Lenhador
        self.MAX_STONES = 10   # Limite de Pedras (Construtor)
        self.MAX_FENCES = 5    # Limite de Cercas Prontas (Construtor)

    def parse(self, inventory_json):
        """Converte JSON para dicionário garantindo que todas as chaves existam."""
        default_inv = {
            "potatoes": 0, 
            "seeds": 0, 
            "logs": 0, 
            "stones": 0, 
            "fences": 0, 
            "plobs": 50.0
        }
        
        if not inventory_json:
            return default_inv
            
        try:
            inv = inventory_json if isinstance(inventory_json, dict) else json.loads(inventory_json)
            # Mescla com o default para garantir chaves faltantes
            for key, value in default_inv.items():
                if key not in inv:
                    inv[key] = value
            return inv
        except:
            return default_inv

    def to_string(self, inv_dict):
        return json.dumps(inv_dict)

    def add_harvest(self, inv_dict):
        """O rendimento de um bloco maduro: 1 Batata e 2 Sementes."""
        inv_dict['potatoes'] = min(self.MAX_POTATOES, inv_dict.get('potatoes', 0) + 1)
        inv_dict['seeds'] = min(self.MAX_SEEDS, inv_dict.get('seeds', 0) + 2)
        return inv_dict

    def has_food(self, inv_dict):
        return inv_dict.get('potatoes', 0) > 0
        
    def has_seeds(self, inv_dict):
        return inv_dict.get('seeds', 0) > 0

    def consume_potato(self, inv_dict):
        if inv_dict.get('potatoes', 0) > 0:
            inv_dict['potatoes'] -= 1
            return True
        return False

    def needs_replenish(self, inv_dict):
        """Verifica se algum recurso básico está abaixo do limite."""
        # A IA quer manter o estoque de batatas sempre cheio
        return inv_dict.get('potatoes', 0) < self.MAX_POTATOES

    # === NOVOS MÉTODOS DE CONTROLE DE MATERIAIS ===
    
    def can_collect_log(self, inv_dict):
        return inv_dict.get('logs', 0) < self.MAX_LOGS

    def can_collect_stone(self, inv_dict):
        return inv_dict.get('stones', 0) < self.MAX_STONES

    def can_carry_fence(self, inv_dict):
        return inv_dict.get('fences', 0) < self.MAX_FENCES