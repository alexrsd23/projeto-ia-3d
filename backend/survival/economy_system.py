import math

class EconomySystem:
    def __init__(self):
        # Aumentamos o valor da cerca para garantir a margem de lucro
        self.BASE_PRICES = {
            "potatoes": 5.0, 
            "seeds": 2.0, 
            "logs": 4.5,    # Matéria-prima (X2 = 9.0)
            "stones": 6.0, 
            "fences": 13.5  # Produto Final (> 9.0 para lucro real)
        }
        self.STARTING_PLOBS = 50.0

    def evaluate_item_value(self, item_type: str, agent_inv: dict, current_hunger: float, trait_lie: float):
        """Calcula o Valuation (Preço Teto ou Piso) baseado no desespero e ganância."""
        base_value = self.BASE_PRICES.get(item_type, 1.0)
        greed_margin = (trait_lie / 100.0) * 0.5 
        
        item_qty = agent_inv.get(item_type, 0)
        scarcity_multiplier = 1.5 if item_qty == 0 else (0.8 if item_qty > 10 else 1.0)
            
        # Fome vai de 100 (Cheio) a 0 (Morte). O desespero inverte isso:
        biological_need = (100.0 - current_hunger) / 100.0 
        urgency_multiplier = 1.0 + biological_need

        subjective_value = base_value * (1.0 + greed_margin) * scarcity_multiplier * urgency_multiplier
        return round(subjective_value, 2)

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