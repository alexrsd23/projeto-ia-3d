from fastapi import APIRouter, HTTPException
import json
import random
import math
import traceback 
from database import driver
from ai_navigation import AgentController, RewardSystem, EnvironmentSensor

router = APIRouter(prefix="/api", tags=["Simulation"])

ai_controller = AgentController()
heatmap_data = {} 

@router.post("/tick")
def simulate_tick():
    try:
        with driver.session() as session:
            # 1. Busca as Entidades
            query_entities = "MATCH (e:Entity) RETURN e.id AS id, e.type AS type, e.posX AS x, e.posZ AS z, e.name AS name"
            results = session.run(query_entities).data()
            
            # Filtro de Segurança
            characters = [r for r in results if r['type'] == 'character' and r.get('x') is not None and r.get('z') is not None]
            cactuses = [r for r in results if r['type'] == 'cactus' and r.get('x') is not None and r.get('z') is not None]
            houses = [r for r in results if r['type'] == 'house' and r.get('x') is not None and r.get('z') is not None]
            
            # 2. Busca as Plantações (Batatas)
            query_tiles = "MATCH (t:Tile {type: 'farm'}) RETURN t.id AS id, t.gridX AS x, t.gridZ AS z, t.cropsJSON AS cropsJSON"
            tiles_result = session.run(query_tiles).data()
            potatoes = []
            for t in tiles_result:
                if t.get('x') is not None and t['cropsJSON'] and json.loads(t['cropsJSON']):
                    potatoes.append((t['x'], t['z']))

            updates_positions = []
            updates_names = []
            dead_agents = []
            last_action_taken = 0 

            # 3. Lógica dos Agentes
            for char in characters:
                target = (0.0, 0.0) if not potatoes else min(potatoes, key=lambda p: math.hypot(p[0]-char['x'], p[1]-char['z']))
                dist_to_target = math.hypot(target[0]-char['x'], target[1]-char['z'])
                
                # =================================================================
                # FIX 1: O IdleState DEVE vir antes de iniciar o episódio!
                # Isso impede que os agentes fiquem parados a criar episódios "fantasmas"
                # =================================================================
                if potatoes and dist_to_target <= 0.1:
                    continue 

                agent_name = char.get('name')
                if not agent_name or agent_name == "None":
                    agent_name = 'Agente Antigo'
                
                mode, is_new = ai_controller.analytics.start_episode(char['id'], char['x'], char['z'])
                
                if is_new:
                    agent_name = f"Explorador {random.randint(10,99)}" if mode == 'explore' else f"Agente {random.randint(10,99)}"
                    updates_names.append({"id": char['id'], "name": agent_name})
                    char['name'] = agent_name
                
                new_x, new_z, action, old_state = ai_controller.process_tick(char['id'], (char['x'], char['z']), target)
                last_action_taken = action

                ai_controller.analytics.record_step(char['id'], action, new_x, new_z)

                is_out_of_bounds = new_x < -24 or new_x > 24 or new_z < -24 or new_z > 24
                hit_cactus = any(math.hypot(new_x - c['x'], new_z - c['z']) < 1.0 for c in cactuses)
                is_collision = any(math.hypot(new_x - h['x'], new_z - h['z']) < 1.5 for h in houses)
                
                new_dist = math.hypot(target[0]-new_x, target[1]-new_z)
                
                # =================================================================
                # FIX 2: Blindagem contra Suicídio Premiado.
                # Só pode ser considerado "Sucesso" se estiver dentro do mapa e vivo!
                # =================================================================
                reached_target = bool(potatoes and new_dist <= 0.1 and not is_out_of_bounds and not is_collision and not hit_cactus)
                
                # A RewardSystem agora vai punir severamente as quedas antes de sequer olhar para a batata
                reward, done = RewardSystem.calculate(new_x, new_z, is_collision, is_out_of_bounds, hit_cactus, ai_controller.shared_knowledge, reached_target)
                
                # =================================================================
                # FIX 3: O Gradiente aplica-se SEMPRE!
                # Isso ensina a IA que o passo diagonal final (+508pts) é melhor que o passo reto final (+506pts)
                # =================================================================
                if not is_out_of_bounds and not is_collision and not hit_cactus:
                    dist_saved = dist_to_target - new_dist
                    if dist_saved > 0:
                        reward += dist_saved * 3.0 

                new_state = EnvironmentSensor.get_state((new_x, new_z), target, ai_controller.shared_knowledge)
                ai_controller.brain.train(old_state, action, reward, new_state, done)
                
                if done:
                    # ===============================================================
                    # NOVO: FIM DO EPISÓDIO (Valida a rota, pontua e envia para análise)
                    # ===============================================================
                    ai_controller.analytics.finalize_episode(char['id'], reached_target, agent_name)
                    
                    if reached_target:
                        # Mostra no Log a quantidade de ticks (passos) que o agente demorou a chegar ao fim
                        steps_taken = ai_controller.analytics.best_routes.get((float(char['x']), float(char['z'])), {}).get('steps', '?')
                        ai_controller.logger.log("INFO", f"🎯 {agent_name} encontrou o recurso em {steps_taken} ticks!")
                        
                        updates_positions.append({"id": char['id'], "x": float(new_x), "z": float(new_z)})
                        heatmap_data[(float(new_x), float(new_z))] = heatmap_data.get((float(new_x), float(new_z)), 0) + 1
                    else:
                        dead_agents.append(char['id'])
                        ai_controller.shared_knowledge.mark_danger(new_x, new_z)
                        if hit_cactus:
                            ai_controller.logger.log("ERROR", f"☠️ {agent_name} colidiu com um cacto em X:{new_x} Z:{new_z}")
                        elif is_out_of_bounds:
                            ai_controller.logger.log("WARNING", f"⚠️ {agent_name} caiu da borda do mundo!")
                
                elif not is_collision:
                    updates_positions.append({"id": char['id'], "x": float(new_x), "z": float(new_z)})
                    coord = (float(new_x), float(new_z))
                    heatmap_data[coord] = heatmap_data.get(coord, 0) + 1

            # 4. Biologia: Crescimento das Plantas
            tiles_to_update = []
            for tile in tiles_result:
                if not tile['cropsJSON']: continue
                crops = json.loads(tile['cropsJSON'])
                changed = False
                for crop in crops:
                    if crop['stage'] < 2 and random.random() < 0.15: 
                        crop['stage'] += 1
                        changed = True
                if changed:
                    tiles_to_update.append({"id": tile['id'], "cropsJSON": json.dumps(crops)})

            # 5. Banco de Dados: Aplica as Deleções e Movimentações
            if dead_agents:
                session.run("MATCH (e:Entity) WHERE e.id IN $ids DETACH DELETE e", ids=dead_agents)
            
            # NOVO: Grava a mudança de nome no Neo4j
            if updates_names:
                session.run("""
                UNWIND $updates AS update
                MATCH (c:Entity {id: update.id})
                SET c.name = update.name
                """, updates=updates_names)
            if updates_positions:
                session.run("""
                UNWIND $updates AS update
                MATCH (c:Entity {id: update.id})
                SET c.posX = update.x, c.posZ = update.z
                """, updates=updates_positions)
            if tiles_to_update:
                session.run("""
                UNWIND $updates AS update
                MATCH (t:Tile {id: update.id})
                SET t.cropsJSON = update.cropsJSON
                """, updates=tiles_to_update)

        safe_heatmap = [{"gridX": float(k[0]), "gridZ": float(k[1]), "visits": int(v)} for k, v in heatmap_data.items()]

        # ===============================================================
        # NOVO: Injetamos o "analytics" na resposta JSON enviada ao React!
        # ===============================================================
        return {
            "message": "Tick processado", 
            "heatmap": safe_heatmap,
            "events": ai_controller.logger.flush(),
            "lastAction": int(last_action_taken),
            "analytics": ai_controller.analytics.get_telemetry_data(ai_controller.shared_knowledge) 
        }
    except Exception as e:
        print("\n🚨 ERRO CRÍTICO NO TICK 🚨")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Rota Isolada de Expurgo
@router.post("/kill-agents")
def kill_all_agents():
    """Mata todos os agentes no banco de dados, mas preserva a memória da IA"""
    try:
        with driver.session() as session:
            # Apaga apenas os personagens. Mantém casas, cactos e plantações.
            session.run("MATCH (c:Entity {type: 'character'}) DETACH DELETE c")
        
        # Regista o evento heroico/trágico no log do frontend
        ai_controller.logger.log("WARNING", "☠️ EXPURGO: Todos os agentes foram eliminados. O Aprendizado foi retido na Mente Global.")
        
        return {"message": "Expurgo concluído!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ===============================================================
# NOVO: Rota para Limpar APENAS a Memória da IA
# ===============================================================
@router.post("/clear-ai-memory")
def clear_ai_memory():
    """Apaga a memória da IA (RAM) sem matar os agentes físicos no banco"""
    global ai_controller
    global heatmap_data
    
    try:
        # LOBOTOMIA: Substitui o cérebro antigo por um cérebro bebé "em branco"
        ai_controller = AgentController()
        heatmap_data = {} 
        
        ai_controller.logger.log("WARNING", "🧠 AMNÉSIA INDUZIDA: A memória de rotas da IA foi completamente apagada!")
        
        return {"message": "Memória da IA limpa com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))