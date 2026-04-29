class MarketIntelligence:
    def __init__(self, economy_system, biology_system):
        self.economy = economy_system
        self.biology = biology_system

    def calculate_energy_cost(self, agent_hunger, trait_lie):
        """
        Calcula o custo monetário subjetivo de 1 unidade de Fome (Caloria).
        Baseia-se no valor atual da batata no mercado para este agente.
        """
        # Qual o valor subjetivo de uma batata AGORA para este agente?
        subjective_potato_price = self.economy.evaluate_item_value("potatoes", {}, agent_hunger, trait_lie)
        
        # Custo por ponto de fome = Preço da Batata / Nutrição da Batata
        cost_per_hunger_point = subjective_potato_price / self.biology.POTATO_NUTRITION
        return cost_per_hunger_point

    def should_work(self, profession, agent_hunger, trait_lie):
        """
        Análise de Custo de Oportunidade (Microeconomia Rigorosa).
        Retorna True se o Lucro Líquido Real cobrir as calorias gastas para trabalhar.
        """
        cost_per_hunger = self.calculate_energy_cost(agent_hunger, trait_lie)
        energy_expenditure = self.biology.ACTION_COST + self.biology.MOVE_COST
        monetary_cost_of_working = energy_expenditure * cost_per_hunger

        if profession == "Lenhador":
            # Calcula a receita COM a inflação atual da madeira
            inflated_log_price = self.economy.BASE_PRICES["logs"] * self.economy.GLOBAL_SCARCITY.get("logs", 1.0)
            return inflated_log_price > (monetary_cost_of_working * 1.2)
            
        elif profession == "Construtor":
            # O Construtor precisa deduzir o custo de reposição da matéria-prima!
            inflated_fence_price = self.economy.BASE_PRICES["fences"] * self.economy.GLOBAL_SCARCITY.get("fences", 1.0)
            inflated_log_cost = self.economy.BASE_PRICES["logs"] * self.economy.GLOBAL_SCARCITY.get("logs", 1.0)
            
            # O lucro real de fazer uma cerca é o preço de venda menos o custo de 2 troncos
            expected_profit = inflated_fence_price - (inflated_log_cost * 2)
            
            # Se o mercado de madeira estiver tão inflacionado que o lucro é zero ou negativo, ele entra em greve IMEDIATAMENTE
            if expected_profit <= 0:
                return False
                
            return expected_profit > (monetary_cost_of_working * 1.2)
        
        elif profession == "Ferreiro":
            # Calcula a margem de forjar Metal
            inflated_part_price = self.economy.BASE_PRICES["metal_parts"] * self.economy.GLOBAL_SCARCITY.get("metal_parts", 1.0)
            inflated_stone_cost = self.economy.BASE_PRICES["stones"] * self.economy.GLOBAL_SCARCITY.get("stones", 1.0)
            profit_metal = inflated_part_price - (inflated_stone_cost * 2)
            
            # Calcula a margem de forjar Kits de Reflorestamento (Lembrete: 1 pedra = 2 sementes)
            inflated_seed_price = self.economy.BASE_PRICES["tree_seed"] * self.economy.GLOBAL_SCARCITY.get("tree_seed", 1.0)
            profit_seed = (inflated_seed_price * 2) - inflated_stone_cost
            
            # Se a melhor das duas opções for rentável, ele trabalha!
            best_profit = max(profit_metal, profit_seed)
            if best_profit <= 0: return False
            return best_profit > (monetary_cost_of_working * 1.2)
            
        elif profession == "Fazendeiro":
            # O Fazendeiro produz do zero, mas gera 2 batatas por bloco plantado
            inflated_potato_price = self.economy.BASE_PRICES["potatoes"] * self.economy.GLOBAL_SCARCITY.get("potatoes", 1.0)
            expected_revenue = inflated_potato_price * 2 
            return expected_revenue > (monetary_cost_of_working * 1.2)
            
        return True