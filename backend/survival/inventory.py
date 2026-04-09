import json

class InventorySystem:
    def __init__(self):
        self.MAX_POTATOES = 4
        self.MAX_SEEDS = 4

    def parse(self, inventory_json):
        if not inventory_json:
            return {"potatoes": 0, "seeds": 0}
        try:
            if isinstance(inventory_json, dict):
                return inventory_json
            return json.loads(inventory_json)
        except:
            return {"potatoes": 0, "seeds": 0}

    def to_string(self, inv_dict):
        return json.dumps(inv_dict)

    def add_harvest(self, inv_dict):
        """O rendimento de um bloco maduro: 1 Batata e 2 Sementes"""
        inv_dict['potatoes'] = min(self.MAX_POTATOES, inv_dict.get('potatoes', 0) + 1)
        inv_dict['seeds'] = min(self.MAX_SEEDS, inv_dict.get('seeds', 0) + 2)
        return inv_dict

    def consume_potato(self, inv_dict):
        """Tenta comer da reserva de emergência"""
        if inv_dict.get('potatoes', 0) > 0:
            inv_dict['potatoes'] -= 1
            return True
        return False

    def consume_seed(self, inv_dict):
        """Usa uma semente para arar/plantar"""
        if inv_dict.get('seeds', 0) > 0:
            inv_dict['seeds'] -= 1
            return True
        return False
        
    def needs_replenish(self, inv_dict):
        """A IA sente-se insegura se não tiver o estoque cheio"""
        return inv_dict.get('potatoes', 0) < self.MAX_POTATOES
        
    def has_food(self, inv_dict):
        return inv_dict.get('potatoes', 0) > 0
        
    def has_seeds(self, inv_dict):
        return inv_dict.get('seeds', 0) > 0