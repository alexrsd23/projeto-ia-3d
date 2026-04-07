from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "admin123" # <-- NÃO ESQUEÇA DE COLOCAR SUA SENHA DO NEO4J AQUI!

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))