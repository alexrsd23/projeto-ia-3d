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
        
        # === NOVOS PARÂMETROS DE VELHICE ===
        self.SENESCENCE_AGE = 1500  # Começa a ficar frágil (Equivalente a ~60 anos)
        self.MAX_AGE = 2500         # O limite biológico máximo (Equivalente a ~100 anos)

    def process_tick(self, agent_data, last_action_type="IDLE"):
        import random
        
        hunger = float(agent_data.get('hunger', self.MAX_HUNGER))
        health = float(agent_data.get('hp', self.MAX_HEALTH))
        age = int(agent_data.get('age', 0)) # O relógio começa
        
        # 1. Envelhecimento
        new_age = age + 1
        
        # 2. Metabolismo
        energy_spent = self.BASE_METABOLISM
        if last_action_type == "MOVE": energy_spent += self.MOVE_COST
        elif last_action_type == "ACTION": energy_spent += self.ACTION_COST

        new_hunger = max(0.0, hunger - energy_spent)
        new_health = health
        death_reason = None

        # 3. Danos (Fome)
        if new_hunger == 0.0:
            new_health = max(0.0, health - self.STARVATION_DAMAGE)
            if new_health <= 0: death_reason = "STARVATION"

        # 4. A Foice do Tempo (Morte Natural)
        if new_health > 0: # Se ainda estiver vivo
            if new_age > self.SENESCENCE_AGE:
                # O risco aumenta de 0 até 1 à medida que se aproxima do MAX_AGE
                risk_factor = (new_age - self.SENESCENCE_AGE) / (self.MAX_AGE - self.SENESCENCE_AGE)
                
                # Sorteio biológico fatal (Até 1% de chance de falecer por tick nos últimos dias de vida)
                if random.random() < (0.01 * risk_factor):
                    new_health = 0.0
                    death_reason = "OLD_AGE"
                    
            if new_age >= self.MAX_AGE: # Ninguém escapa à matemática final
                new_health = 0.0
                death_reason = "OLD_AGE"

        return {
            "hunger": round(new_hunger, 1),
            "hp": round(new_health, 1),
            "age": new_age,
            "is_dead": new_health <= 0.0,
            "death_reason": death_reason
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
        
    def mix_dna(self, parent_a: dict, parent_b: dict) -> dict:
        # Mendel 2.0: Mistura a genética de dois agentes para criar um filho com traços únicos e mutações.
        import random
        
        # 1. Genética Biológica (Sexo e Profissão)
        # O sexo é 50/50 puro.
        child_sex = random.choice(['M', 'F'])
        # A profissão é herdada por tradição (como eles têm de ter a mesma para casar, a criança herda)
        child_profession = parent_a.get('profession', 'Explorador')
        
        # 2. Mistura de Cores (Aquarela Genética)
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) != 6: return (128, 128, 128) # Gray default
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
        def rgb_to_hex(rgb):
            return '#%02x%02x%02x' % tuple(int(max(0, min(255, c))) for c in rgb)

        color_a = hex_to_rgb(parent_a.get('color', '#808080'))
        color_b = hex_to_rgb(parent_b.get('color', '#808080'))
        
        # O filho é a média das cores dos pais + uma ligeira mutação (-15 a +15 em cada canal de cor)
        child_rgb = [
            (color_a[i] + color_b[i]) / 2 + random.randint(-15, 15) 
            for i in range(3)
        ]
        child_color = rgb_to_hex(child_rgb)
        
        # 3. Herança Comportamental (Natureza + Mutação/Nurture)
        # === CORREÇÃO: Genética Dominante (Mendel) ===
        # A criança herda 100% do gene de um dos pais aleatoriamente, e sofre uma mutação.
        def mix_trait(trait_name):
            val_a = float(parent_a.get(trait_name, 50.0))
            val_b = float(parent_b.get(trait_name, 50.0))
            
            # Sorteia qual genitor passará o gene dominante
            base_gene = random.choice([val_a, val_b])
            
            # Aplica a mutação (livre arbítrio / fatores externos)
            mutation = random.uniform(-15.0, 15.0)
            return max(0.0, min(100.0, base_gene + mutation)) # Garante que fica entre 0 e 100

        child_trust = mix_trait('trustLevel')
        child_lie = mix_trait('lieLevel')
        
        return {
            "sex": child_sex,
            "profession": child_profession,
            "color": child_color,
            "trustLevel": round(child_trust, 1),
            "lieLevel": round(child_lie, 1),
            "married": False # Nasce solteiro, claro!
        }