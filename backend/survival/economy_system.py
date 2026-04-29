import math

class EconomySystem:
    # === NOVO: Variáveis de Classe para persistir a escassez global ===
    GLOBAL_SCARCITY = {
        "potatoes": 1.0, 
        "seeds": 1.0, 
        "logs": 1.0,    
        "stones": 1.0, 
        "fences": 1.0,
        "gates": 1.0,
        "metal_parts": 1.0,
        "tool_repair": 1.0,
        "tree_seed": 1.0  # <--- NOVO: O Kit de Plantio
    }

    def __init__(self):
        self.BASE_PRICES = {
            "potatoes": 8.0, 
            "seeds": 2.0, 
            "logs": 4.0,    
            "stones": 4.0, 
            "metal_parts": 12.0,
            "fences": 12.5,
            "gates": 42.0,
            "tool_repair": 20.0,
            "tree_seed": 8.0   # <--- NOVO: Preço de mercado (Altamente rentável para o Ferreiro)
        }
        # Injeção de Capital! Impede que a economia quebre na primeira geração de construções
        self.STARTING_PLOBS = 500.0

    @classmethod
    def register_scarcity(cls, item_type: str):
        """Aumenta a inflação do item em 10% sempre que um negócio falha por falta ou preço. Teto máximo de 500%."""
        if item_type in cls.GLOBAL_SCARCITY:
            # === CORREÇÃO: Previne hiperinflação ilimitada limitando o multiplicador a 5.0 ===
            cls.GLOBAL_SCARCITY[item_type] = min(5.0, cls.GLOBAL_SCARCITY[item_type] + 0.10)

    @classmethod
    def cool_down_market(cls):
        """Esfria o mercado ativamente a cada tick para corrigir bolhas inflacionárias."""
        for k in cls.GLOBAL_SCARCITY:
            if cls.GLOBAL_SCARCITY[k] > 1.0:
                # === CORREÇÃO: Amortização aumentada de 0.01 para 0.05 ===
                # Isso garante que um pico de preço falso se corrija em 20 ticks
                cls.GLOBAL_SCARCITY[k] = max(1.0, round(cls.GLOBAL_SCARCITY[k] - 0.05, 2))

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

    def negotiate_deal(self, buyer, seller, item_type, qty=1, buyer_name="Comprador", seller_name="Vendedor"):
        """
        Leilão Bilateral Estruturado com Log Conversacional e Metadados.
        """
        b_inv = buyer.get('inventoryJSON', {})
        s_inv = seller.get('inventoryJSON', {})
        chat_log = []
        
        chat_log.append(f"💰 NEGOCIAÇÃO: {buyer_name} abordou {seller_name} para negociar '{item_type}'.")

        # 1. Limites Absolutos da ZOPA
        max_willing_to_pay = self.evaluate_item_value(item_type, b_inv, buyer.get('hunger', 100), buyer.get('lieLevel', 0))
        min_willing_to_accept = self.evaluate_item_value(item_type, s_inv, seller.get('hunger', 100), seller.get('lieLevel', 0))

        if max_willing_to_pay < min_willing_to_accept:
            chat_log.append(f"🗣️ {buyer_name}: 'Pago no máximo {max_willing_to_pay:.2f} Plobs.'")
            chat_log.append(f"🗣️ {seller_name}: 'Por menos de {min_willing_to_accept:.2f} Plobs eu não vendo.'")
            chat_log.append(f"💔 MERCADO: Impasse total! Fora da zona de possível acordo.")
            # O retorno de falha já estava correto na nossa lógica anterior
            return {"success": False, "reason": "Fora da ZOPA", "chat_log": chat_log, "buyer_ceiling": max_willing_to_pay, "seller_floor": min_willing_to_accept}

        # 2. Ancoragem de Ofertas Iniciais
        base_market_price = self.BASE_PRICES.get(item_type, 1.0) * self.GLOBAL_SCARCITY.get(item_type, 1.0)
        buyer_offer = max(0.1, min(max_willing_to_pay, base_market_price * 0.8))
        seller_ask = max(min_willing_to_accept, base_market_price * 1.2)

        # 3. Loop de Negociação Bidirecional
        max_rounds = 5
        for round_num in range(max_rounds):
            chat_log.append(f"🗣️ LANCE (Rodada {round_num+1}) | {buyer_name}: 'Ofereço {buyer_offer:.2f}' | {seller_name}: 'Faço por {seller_ask:.2f}'")
            
            if buyer_offer >= seller_ask:
                final_price = (buyer_offer + seller_ask) / 2
                chat_log.append(f"🤝 MERCADO: Ofertas colidiram! Acordo fechado por {final_price:.2f} Plobs.")
                # === CORREÇÃO: Reintegração das chaves de teto e piso ===
                return {
                    "success": True, 
                    "price": round(final_price, 2), 
                    "buyer_ceiling": max_willing_to_pay, 
                    "seller_floor": min_willing_to_accept,
                    "chat_log": chat_log
                }

            buyer_urgency = 1.5 if buyer.get('hunger', 100) < 50 else 1.0
            buyer_concession = 0.10 * buyer_urgency
            seller_stubbornness = seller.get('lieLevel', 0) / 100.0
            seller_concession = 0.15 * (1.0 - (seller_stubbornness * 0.5))

            buyer_offer = min(max_willing_to_pay, buyer_offer * (1.0 + buyer_concession))
            seller_ask = max(min_willing_to_accept, seller_ask * (1.0 - seller_concession))

        # 4. Fallback de Segurança
        lie_advantage = (seller.get('lieLevel', 0) - buyer.get('lieLevel', 0)) / 100.0
        mid_point = (max_willing_to_pay + min_willing_to_accept) / 2
        final_price = mid_point + (lie_advantage * (max_willing_to_pay - min_willing_to_accept) / 2)
        
        chat_log.append(f"🤝 MERCADO: Após muito custo, as partes concordaram em {final_price:.2f} Plobs.")
        # === CORREÇÃO: Reintegração das chaves de teto e piso ===
        return {
            "success": True, 
            "price": round(final_price, 2), 
            "buyer_ceiling": max_willing_to_pay, 
            "seller_floor": min_willing_to_accept,
            "chat_log": chat_log
        }
        
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