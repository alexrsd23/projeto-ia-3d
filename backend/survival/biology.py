# =====================================================================
# SISTEMA BIOLÓGICO: Controla o Metabolismo, Fome e Vida dos Agentes
# =====================================================================

class BiologySystem:
    def __init__(self):
        self.MAX_HUNGER = 100.0
        self.MAX_HEALTH = 100.0
        
        # === NOVO BALANÇO METABÓLICO (Fome 10x mais lenta) ===
        self.BASE_METABOLISM = 0.02   # Quase não gasta se estiver parado
        self.MOVE_COST = 0.08         # Total de 0.1 por tick a andar (Sobrevive 1000 ticks / ~4 minutos)
        self.ACTION_COST = 0.50       # Trabalho pesado (arar/plantar) cansa 5x mais rápido
        
        self.STARVATION_DAMAGE = 3.0  
        self.POTATO_NUTRITION = 35.0  # Nutrição ajustada para exigir múltiplas refeições

    def process_tick(self, agent_data, last_action_type="IDLE"):
        """
        Processa o desgaste biológico do agente num único tick.
        last_action_type pode ser: "IDLE" (Parado), "MOVE" (Andando) ou "ACTION" (Trabalhando)
        """
        hunger = float(agent_data.get('hunger', self.MAX_HUNGER))
        health = float(agent_data.get('hp', self.MAX_HEALTH))

        # 1. Calcula o Custo Energético
        energy_spent = self.BASE_METABOLISM
        if last_action_type == "MOVE":
            energy_spent += self.MOVE_COST
        elif last_action_type == "ACTION":
            energy_spent += self.ACTION_COST

        # 2. Aplica o desgaste da Fome
        new_hunger = max(0.0, hunger - energy_spent)

        # 3. Aplica o Dano por Inanição (Morte por fome)
        new_health = health
        if new_hunger == 0.0:
            new_health = max(0.0, health - self.STARVATION_DAMAGE)

        return {
            "hunger": round(new_hunger, 1),
            "hp": round(new_health, 1),
            "is_dead": new_health <= 0.0
        }

    def consume_food(self, agent_data, food_type="POTATO"):
        """
        Processa a ingestão de alimentos, recuperando fome e curando ferimentos leves.
        """
        hunger = float(agent_data.get('hunger', 0.0))
        health = float(agent_data.get('hp', 0.0))
        
        nutrition = self.POTATO_NUTRITION if food_type == "POTATO" else 10.0
        
        # Recupera a fome até ao limite máximo
        new_hunger = min(self.MAX_HUNGER, hunger + nutrition)
        
        # A comida também tem um ligeiro efeito curativo (20% da nutrição vira vida)
        healing_factor = nutrition * 0.2
        new_health = min(self.MAX_HEALTH, health + healing_factor)

        return {
            "hunger": round(new_hunger, 1),
            "hp": round(new_health, 1)
        }