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
        Análise de Custo de Oportunidade.
        Retorna True se o lucro esperado cobrir as calorias gastas para trabalhar.
        """
        cost_per_hunger = self.calculate_energy_cost(agent_hunger, trait_lie)
        
        # Trabalhar gasta ACTION_COST (0.5). Andar gasta MOVE_COST (0.08). Total = ~0.6 por ação produtiva.
        energy_expenditure = self.biology.ACTION_COST + self.biology.MOVE_COST
        monetary_cost_of_working = energy_expenditure * cost_per_hunger

        if profession == "Lenhador":
            # Lenhador espera extrair 1 Tronco (Log)
            expected_revenue = self.economy.BASE_PRICES["logs"]
            # Exige uma margem de segurança de 20%
            return expected_revenue > (monetary_cost_of_working * 1.2)
            
        elif profession == "Construtor":
            # Construtor cobra pelo reparo (ex: valor da cerca / 2)
            expected_revenue = self.economy.BASE_PRICES["fences"] * 0.5
            return expected_revenue > (monetary_cost_of_working * 1.2)
            
        return True # Fazendeiro trabalha sempre, pois ele gera a própria base da moeda (comida)