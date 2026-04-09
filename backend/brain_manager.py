from ai_navigation import AgentController
from survival.survival_brain import SurvivalController

class BrainManager:
    def __init__(self):
        self.current_mode = "ROUTES"  # Começa sempre no Modo Rotas
        
        # Instanciamos os dois cérebros de forma TOTALMENTE isolada.
        # Eles não compartilham Rede Neural, Replay Buffer ou Heatmap.
        self.routes_brain = AgentController()
        self.survival_brain = SurvivalController()

    def switch_mode(self, new_mode: str):
        valid_modes = ["ROUTES", "SURVIVAL"]
        if new_mode not in valid_modes:
            raise ValueError(f"Modo '{new_mode}' não existe. Escolha entre {valid_modes}.")
        
        self.current_mode = new_mode
        print(f"🧠 Cérebro alterado para: {self.current_mode}")

    def reset_memory(self):
        """Lobotoma apenas o cérebro que está ativo no momento"""
        if self.current_mode == "ROUTES":
            self.routes_brain = AgentController()
            print("⚠️ Memória do Modo ROTAS apagada.")
        elif self.current_mode == "SURVIVAL":
            self.survival_brain = SurvivalController()
            print("⚠️ Memória do Modo SOBREVIVÊNCIA apagada.")

# Instância global para ser importada por toda a aplicação FastAPI
manager = BrainManager()