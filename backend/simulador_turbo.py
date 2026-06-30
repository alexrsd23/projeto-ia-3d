import time
import json
from database import driver
from brain_manager import manager
from survival.survival_engine import process_survival_tick

def run_headless_simulation(target_ticks=100000):
    print(f"🚀 INICIANDO SIMULAÇÃO MACRO (HEADLESS): {target_ticks} TICKS")
    
    # Garante que o cérebro está configurado para o modo de sobrevivência
    manager.current_mode = "SURVIVAL"
    
    start_time = time.time()
    
    with driver.session() as session:
        for tick in range(1, target_ticks + 1):
            
            # 1. Executa o Tick exatamente como a API faria
            result = process_survival_tick(manager.survival_brain, session)
            
            # 2. O FILTRO DE VISÃO
            for event in result.get('events', []):
                msg = event['message']
                if any(icon in msg for icon in ['🌍', '☠️', '⚰️', '👶', '💍', '🏚️', '🧬']):
                    print(f"[Tick {tick:06d}] {msg}")
            
            # 3. O RELATÓRIO DO SÉCULO
            if tick % 1000 == 0:
                print(f"\n{'='*60}")
                print(f"📊 RELATÓRIO DO SÉCULO (Tick {tick})")
                print(f"{'='*60}")
                
                agentes_db = session.run("""
                    MATCH (e:Entity)
                    WHERE e.type IN ['farmer', 'woodcutter', 'builder', 'blacksmith', 'wolf']
                    RETURN e.type AS type, e.inventoryJSON AS inv
                """).data()
                
                censo = {'farmer': 0, 'woodcutter': 0, 'builder': 0, 'blacksmith': 0, 'wolf': 0}
                total_plobs = 0.0
                total_potatoes = 0
                
                for a in agentes_db:
                    censo[a['type']] += 1
                    if a['type'] != 'wolf':
                        try:
                            inv = json.loads(a['inv'])
                            total_plobs += float(inv.get('plobs', 0.0))
                            total_potatoes += int(inv.get('potatoes', 0))
                        except:
                            pass
                
                total_trabalhadores = sum(v for k, v in censo.items() if k != 'wolf')
                media_plobs = (total_plobs / total_trabalhadores) if total_trabalhadores > 0 else 0
                
                bounds = getattr(manager.survival_brain, 'world_bounds', {"minX": -24, "maxX": 24, "minZ": -24, "maxZ": 24})
                
                print(f"🗺️  FRONTEIRAS DO MUNDO: X({bounds['minX']} a {bounds['maxX']}) Z({bounds['minZ']} a {bounds['maxZ']})")
                print("👥 CENSO POPULACIONAL:")
                print(f"  🌾 Fazendeiros: {censo['farmer']} | 🪓 Lenhadores: {censo['woodcutter']}")
                print(f"  🧱 Construtores: {censo['builder']} | ⚒️ Ferreiros: {censo['blacksmith']}")
                print(f"  🐺 Lobos: {censo['wolf']}")
                print("\n💰 MACROECONOMIA:")
                print(f"  - Riqueza Média Per Capita: {media_plobs:.2f} Plobs")
                print(f"  - Reserva Global de Batatas: {total_potatoes} unidades")
                print(f"{'='*60}\n")

    end_time = time.time()
    print(f"✅ SIMULAÇÃO CONCLUÍDA! Tempo real decorrido: {(end_time - start_time):.2f} segundos.")

if __name__ == "__main__":
    run_headless_simulation(100000)