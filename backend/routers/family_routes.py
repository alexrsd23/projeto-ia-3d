from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from database import driver

router = APIRouter(prefix="/api/family", tags=["Family Tree & Sociology"])

class MarriageRequest(BaseModel):
    agent_a_id: str
    agent_b_id: str

@router.post("/marry")
def register_marriage(request: MarriageRequest):
    """
    Tenta realizar o casamento entre duas entidades.
    Regras de Negócio: Devem existir, ser solteiros e ter a MESMA profissão.
    """
    query_validate = """
    MATCH (a:Entity {id: $idA}), (b:Entity {id: $idB})
    RETURN a.profession AS profA, a.married AS marriedA, a.name AS nameA,
           b.profession AS profB, b.married AS marriedB, b.name AS nameB
    """
    
    try:
        with driver.session() as session:
            # 1. Busca os pretendentes
            result = session.run(query_validate, idA=request.agent_a_id, idB=request.agent_b_id).data()
            
            if not result:
                raise HTTPException(status_code=404, detail="Um ou ambos os agentes não foram encontrados.")
                
            data = result[0]
            
            # 2. Valida as Regras do Sistema
            if data['marriedA'] == True or data['marriedB'] == True:
                raise HTTPException(status_code=400, detail="A poligamia não é permitida. Um dos agentes já é casado.")
                
            if data['profA'] != data['profB']:
                raise HTTPException(status_code=400, detail=f"Incompatibilidade! {data['profA']} não pode casar com {data['profB']}.")
                
            # 2.5 Validação Genética de Consanguinidade
            query_incest = """
            MATCH (a:Entity {id: $idA}), (b:Entity {id: $idB})
            OPTIONAL MATCH p1=(a)-[:PARENT_OF*1..]->(b)
            OPTIONAL MATCH p2=(b)-[:PARENT_OF*1..]->(a)
            OPTIONAL MATCH p3=(a)<-[:PARENT_OF]-()-[:PARENT_OF]->(b)
            OPTIONAL MATCH p4=(a)<-[:PARENT_OF]-()-[:PARENT_OF]-()-[:PARENT_OF]->(b)
            OPTIONAL MATCH p5=(b)<-[:PARENT_OF]-()-[:PARENT_OF]-()-[:PARENT_OF]->(a)
            RETURN (p1 IS NOT NULL OR p2 IS NOT NULL OR p3 IS NOT NULL OR p4 IS NOT NULL OR p5 IS NOT NULL) AS is_incest
            LIMIT 1
            """
            incest_check = session.run(query_incest, idA=request.agent_a_id, idB=request.agent_b_id).single()
            
            if incest_check and incest_check["is_incest"]:
                raise HTTPException(status_code=400, detail="Tabu Genético! Relações entre parentes em linha reta, irmãos e tios/sobrinhos são estritamente proibidas.")
                
            # 3. Executa o Casamento no Neo4j
            query_marry = """
            MATCH (a:Entity {id: $idA}), (b:Entity {id: $idB})
            // Cria um relacionamento amigável sem direção específica entre os dois
            MERGE (a)-[r:MARRIED_TO]-(b)
            SET a.married = true, b.married = true
            RETURN r
            """
            session.run(query_marry, idA=request.agent_a_id, idB=request.agent_b_id)
            
            return {"message": f"Casamento realizado com sucesso entre {data['nameA']} e {data['nameB']}!"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/tree")
def get_family_tree():
    """
    Retorna o grafo completo da sociedade (Nós e Arestas) para renderizar a Árvore Genealógica.
    Lê vivos e mortos, pois os falecidos são as raízes da árvore.
    """
    # 1. Busca todos os indivíduos que já existiram
    query_nodes = """
    MATCH (n:Entity)
    WHERE n.type IN ['farmer', 'woodcutter', 'builder', 'blacksmith', 'character', 'loot'] AND n.name IS NOT NULL
    RETURN n.id AS id, n.name AS name, n.type AS type, n.profession AS profession, 
           n.color AS color, coalesce(n.married, false) AS married, 
           coalesce(n.age, 0) AS age, coalesce(n.sex, 'M') AS sex,
           (coalesce(n.health, 0) <= 0 OR n.type = 'loot') AS is_dead
    """
    
    # 2. Busca todas as conexões de sangue e amor
    query_edges = """
    MATCH (n:Entity)-[r:PARENT_OF|MARRIED_TO|WIDOWED_FROM]->(m:Entity)
    RETURN n.id AS source, type(r) AS rel_type, m.id AS target
    """
    
    try:
        with driver.session() as session:
            nodes = session.run(query_nodes).data()
            edges = session.run(query_edges).data()
            
            return {
                "nodes": nodes,
                "edges": edges
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/tree/{agent_id}")
def get_individual_family_tree(agent_id: str = Path(..., description="The ID of the individual to view the family tree for")):
    """
    Retorna o grafo da árvore genealógica para um indivíduo específico,
    incluindo ancestrais (até 5 gerações), descendentes (até 5 gerações),
    e todas as parcerias/histórico conjugal desses indivíduos.
    Utiliza uma abordagem de 3 queries simplificadas para performance.
    """
    depth = 5 #geraçoes up/down
    
    # Dentro de get_individual_family_tree()
    query_collect_ids = f"""
    MATCH (n:Entity {{id: $agent_id}})
    OPTIONAL MATCH (n)<-[:PARENT_OF*0..{depth}]-(ancestor:Entity)
    OPTIONAL MATCH (n)-[:PARENT_OF*0..{depth}]->(descendant:Entity)
    WITH n, COLLECT(DISTINCT ancestor) + COLLECT(DISTINCT descendant) AS family_nodes
    UNWIND family_nodes AS node
    MATCH (node)
    WHERE node.type IN ['farmer', 'woodcutter', 'builder', 'blacksmith', 'character', 'loot'] AND node.name IS NOT NULL
    
    // Busca os parceiros diretos de cada nó da família
    OPTIONAL MATCH (node)-[p:MARRIED_TO|WIDOWED_FROM]-(partner:Entity)
    WHERE partner.type IN ['farmer', 'woodcutter', 'builder', 'blacksmith', 'character', 'loot'] AND partner.name IS NOT NULL
    
    // Retorna o conjunto único de IDs de nós da família e seus parceiros
    WITH COLLECT(DISTINCT node.id) + COLLECT(DISTINCT partner.id) AS all_ids
    UNWIND all_ids AS id
    RETURN DISTINCT id
    """

    try:
        with driver.session() as session:
            # 1. Executa a query para IDs
            ids_result = session.run(query_collect_ids, agent_id=agent_id).data()
            relevant_ids = [record['id'] for record in ids_result]
            
            if not relevant_ids:
                return {"nodes": [], "edges": []}

            # 2. Query para Buscar dados completos dos nós relevantes
            query_fetch_nodes = """
            MATCH (n:Entity)
            WHERE n.id IN $relevant_ids
            RETURN DISTINCT n.id AS id, n.name AS name, n.type AS type, n.profession AS profession,
                   n.color AS color, coalesce(n.married, false) AS married,
                   coalesce(n.age, 0) AS age, coalesce(n.sex, 'M') AS sex,
                   n.inventoryJSON AS inventoryJSON, n.health AS health, n.hunger AS hunger,
                   (coalesce(n.health, 0) <= 0 OR n.type = 'loot') AS is_dead
            """
            nodes_data = session.run(query_fetch_nodes, relevant_ids=relevant_ids).data()

            # 3. Query para Buscar arestas *apenas* entre os nós relevantes
            query_fetch_edges = """
            MATCH (n:Entity)-[r:PARENT_OF|MARRIED_TO|WIDOWED_FROM]->(m:Entity)
            WHERE n.id IN $relevant_ids AND m.id IN $relevant_ids
            RETURN DISTINCT n.id AS source, type(r) AS rel_type, m.id AS target
            """
            edges_data = session.run(query_fetch_edges, relevant_ids=relevant_ids).data()
            
            return {
                "nodes": nodes_data,
                "edges": edges_data
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))