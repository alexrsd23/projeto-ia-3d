import json

class InventorySystem:
    def __init__(self):
        # Limites de Estoque
        self.MAX_POTATOES = 16
        self.MAX_SEEDS = 16
        self.MAX_LOGS = 40     # Limite do Lenhador expandido para suprir a demanda
        self.MAX_STONES = 16   # Pedras suficientes para 4 portões
        self.MAX_FENCES = 20   # Cercas suficientes para cercar a fazenda inteira de uma vez
        self.MAX_GATES = 5     # Novo Limite para Portões

    def parse(self, inventory_json):
        """Converte JSON para dicionário garantindo que todas as chaves existam."""
        default_inv = {
            "potatoes": 0, 
            "seeds": 0, 
            "logs": 0, 
            "stones": 0, 
            "fences": 0, 
            "gates": 0,        # <--- NOVO: Chave para os Portões
            "plobs": 500.0
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
    
   
    def consume_seed(self, inv_dict):
        if inv_dict.get('seeds', 0) > 0:
            inv_dict['seeds'] -= 1
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
    
    # === ADICIONE ISTO DENTRO DA CLASSE InventorySystem ===
    def transfer_loot(self, agent_inv, loot_inv):
        """
        Transfere itens do loot para o agente, respeitando os limites da mochila do agente.
        Retorna o inventário do agente atualizado, o loot atualizado e um booleano 
        indicando se o saco de loot ficou completamente vazio.
        """
        # Mapeamento dinâmico dos limites por item
        limits = {
            "potatoes": self.MAX_POTATOES,
            "seeds": self.MAX_SEEDS,
            "logs": self.MAX_LOGS,
            "stones": self.MAX_STONES,
            "fences": self.MAX_FENCES,
            "gates": self.MAX_GATES,
            "plobs": float('inf') # Dinheiro não tem limite de peso
        }
        
        items_transferred = False
        
        for item, amount_in_loot in list(loot_inv.items()):
            if amount_in_loot > 0:
                current_amount = agent_inv.get(item, 0)
                max_capacity = limits.get(item, 0)
                
                # Se o limite do agente for maior que zero para este item (ex: Lenhador tem MAX_LOGS > 0)
                # Ou se for Plobs (sem limite)
                if max_capacity > 0:
                    # Calcula quanto espaço livre o agente tem
                    free_space = max_capacity - current_amount if max_capacity != float('inf') else float('inf')
                    
                    # Transfere apenas o que couber
                    amount_to_transfer = min(amount_in_loot, free_space)
                    
                    if amount_to_transfer > 0:
                        # Se for dinheiro, garante que mantém os decimais, senão converte para inteiro
                        if item == "plobs":
                            agent_inv[item] = round(current_amount + amount_to_transfer, 2)
                            loot_inv[item] = round(amount_in_loot - amount_to_transfer, 2)
                        else:
                            agent_inv[item] = current_amount + int(amount_to_transfer)
                            loot_inv[item] = amount_in_loot - int(amount_to_transfer)
                            
                        items_transferred = True

        # Verifica se o saco ficou vazio (ignora chaves zeradas ou negativas)
        is_empty = sum([val for val in loot_inv.values() if val > 0]) == 0
        
        return agent_inv, loot_inv, is_empty, items_transferred
    
    def craft_seeds(self, inv_dict):
        """
        Converte 1 Batata em 2 Sementes.
        Retorna True se o craft foi bem-sucedido, False caso contrário.
        """
        # Verifica se tem batatas e se tem espaço para pelo menos 1 semente
        if inv_dict.get('potatoes', 0) >= 1 and inv_dict.get('seeds', 0) < self.MAX_SEEDS:
            inv_dict['potatoes'] -= 1
            # Adiciona até 2 sementes, respeitando o limite máximo
            inv_dict['seeds'] = min(self.MAX_SEEDS, inv_dict.get('seeds', 0) + 2)
            return True
        return False