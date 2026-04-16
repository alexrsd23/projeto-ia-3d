import math

class EconomySystem:
    # === NOVO: Variáveis de Classe para persistir a escassez global ===
    GLOBAL_SCARCITY = {
        "potatoes": 1.0, 
        "seeds": 1.0, 
        "logs": 1.0,    
        "stones": 1.0, 
        "fences": 1.0,
        "gates": 1.0     # <--- NOVO
    }

    def __init__(self):
        self.BASE_PRICES = {
            "potatoes": 8.0, 
            "seeds": 2.0, 
            "logs": 4.0,    
            "stones": 4.0, 
            "fences": 12.5,
            "gates": 28.0    # Custo(2 troncos + 4 pedras) = 24. Preço de Venda = 28
        }
        # Injeção de Capital! Impede que a economia quebre na primeira geração de construções
        self.STARTING_PLOBS = 300.0

    @classmethod
    def register_scarcity(cls, item_type: str):
        """Aumenta a inflação do item em 10% sempre que um negócio falha por falta ou preço. Teto máximo de 500%."""
        if item_type in cls.GLOBAL_SCARCITY:
            # === CORREÇÃO: Previne hiperinflação ilimitada limitando o multiplicador a 5.0 ===
            cls.GLOBAL_SCARCITY[item_type] = min(5.0, cls.GLOBAL_SCARCITY[item_type] + 0.10)

    @classmethod
    def cool_down_market(cls):
        """Esfria o mercado em 1% a cada tick para o preço descer se não houver crises."""
        for k in cls.GLOBAL_SCARCITY:
            if cls.GLOBAL_SCARCITY[k] > 1.0:
                cls.GLOBAL_SCARCITY[k] = max(1.0, cls.GLOBAL_SCARCITY[k] - 0.01)

    def evaluate_item_value(self, item_type: str, agent_inv: dict, current_hunger: float, trait_lie: float):
        """Calcula o Valuation baseado no desespero, ganância E inflação global."""
        base_value = self.BASE_PRICES.get(item_type, 1.0)
        
        # === NOVO: Aplica a inflação global sobre o preço base ===
        inflated_base = base_value * self.GLOBAL_SCARCITY.get(item_type, 1.0)
        
        greed_margin = (trait_lie / 100.0) * 0.5 
        item_qty = agent_inv.get(item_type, 0)
        scarcity_multiplier = 1.5 if item_qty == 0 else (0.8 if item_qty > 10 else 1.0)
            
        # Desespero biológico (0 = desespero máximo)
        biological_need = (100.0 - current_hunger) / 100.0 
        desperation_multiplier = 1.0 + (1.0 - biological_need)

        final_value = inflated_base * scarcity_multiplier * desperation_multiplier * (1.0 + greed_margin)
        return round(max(0.1, final_value), 2)

    def negotiate_deal(self, buyer, seller, item_type, qty=1):
        """A Sala de Reuniões: Os dois calculam os seus limites. Se houver margem, fecham negócio."""
        b_inv = buyer.get('inventoryJSON', {})
        s_inv = seller.get('inventoryJSON', {})
        
        # O Máximo que o Comprador aceita pagar (Ele está desesperado?)
        max_willing_to_pay = self.evaluate_item_value(item_type, b_inv, buyer.get('hunger', 100), buyer.get('lieLevel', 0))
        # O Mínimo que o Vendedor aceita receber (Ele está ganancioso?)
        min_willing_to_accept = self.evaluate_item_value(item_type, s_inv, seller.get('hunger', 100), seller.get('lieLevel', 0))

        if max_willing_to_pay >= min_willing_to_accept:
            # Temos um acordo! O preço final é disputado na lábia (Nível de Mentira)
            lie_advantage = (seller.get('lieLevel', 0) - buyer.get('lieLevel', 0)) / 100.0
            mid_price = (max_willing_to_pay + min_willing_to_accept) / 2
            
            # Se o vendedor for mais mentiroso, o preço sobe em direção ao teto do comprador.
            final_price = mid_price + (lie_advantage * (max_willing_to_pay - min_willing_to_accept) / 2)
            
            return {
                "success": True, 
                "price": round(final_price, 2), 
                "buyer_ceiling": max_willing_to_pay, 
                "seller_floor": min_willing_to_accept
            }
        
        return {"success": False, "reason": "Sem acordo financeiro", "buyer_ceiling": max_willing_to_pay, "seller_floor": min_willing_to_accept}

    def execute_trade(self, buyer_inv, seller_inv, item_type, agreed_price, qty=1):
        """Liquidação Financeira e Logística."""
        total_cost = agreed_price * qty
        if buyer_inv.get("plobs", 0.0) < total_cost: return False, buyer_inv, seller_inv, "Fundos insuficientes"
        if seller_inv.get(item_type, 0) < qty: return False, buyer_inv, seller_inv, "Estoque insuficiente"

        buyer_inv["plobs"] = round(buyer_inv.get("plobs", 0.0) - total_cost, 2)
        seller_inv["plobs"] = round(seller_inv.get("plobs", 0.0) + total_cost, 2)
        seller_inv[item_type] -= qty
        buyer_inv[item_type] = buyer_inv.get(item_type, 0) + qty

        return True, buyer_inv, seller_inv, "Transação concluída"