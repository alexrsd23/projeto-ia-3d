from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importando nossos roteadores modulares
from routers import interactions, farming, simulation

app = FastAPI(title="Mundo IA - Backend Modularizado")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectando os módulos ao orquestrador central
app.include_router(interactions.router)
app.include_router(farming.router)
app.include_router(simulation.router)

@app.get("/")
def home():
    return {"status": "Servidor do Mundo IA está online, limpo e desacoplado no Python 3.12!"}