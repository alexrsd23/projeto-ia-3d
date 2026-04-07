from neo4j import GraphDatabase

# O Neo4j local roda por padrão nesta porta (7687) e o usuário padrão é 'neo4j'
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "admin123" # Substitua pela senha que você acabou de criar!

def testar_conexao():
    try:
        # Tenta criar a conexão
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        
        # Pede para o driver verificar se está tudo ok
        driver.verify_connectivity()
        
        print("✅ Conexão com o Neo4j estabelecida com sucesso! O cérebro está ligado ao banco.")
        
        # Fecha a conexão após o teste
        driver.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")

# Executa o teste
if __name__ == "__main__":
    testar_conexao()