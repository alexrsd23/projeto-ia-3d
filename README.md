# 🌍 Mundo IA — Simulador 3D de Ecossistema e Inteligência Artificial Multiagente

> Plataforma avançada de simulação 3D para estudo de Inteligência Artificial, Machine Learning e comportamentos emergentes em sistemas multiagentes.

---

## 📌 Visão Geral

O **Mundo IA** é um ambiente de simulação 3D altamente modular projetado para explorar, comparar e analisar diferentes paradigmas de inteligência artificial dentro de um mesmo ecossistema virtual.

O projeto implementa dois motores cognitivos independentes:

* **Q-Learning** → Agentes orientados por otimização matemática e maximização de recompensa.
* **Biological FSM** → Agentes orientados por sobrevivência, genética, economia e comportamento social.

Essa arquitetura permite observar como diferentes modelos de tomada de decisão impactam a adaptação e a emergência comportamental em populações artificiais.

---

## 🎯 Objetivos do Projeto

* Estudar comportamento emergente em sistemas multiagentes.
* Comparar aprendizado por reforço com máquinas de estado biológicas.
* Simular economia, genética, reprodução e mortalidade em ecossistemas artificiais.
* Criar uma base experimental para pesquisas futuras em IA adaptativa.

---

## 🏗 Arquitetura do Sistema

```text
Frontend (React + Three.js)
        ↓
Backend API (FastAPI)
        ↓
Simulation Engine (Python)
        ↓
Neo4j Graph Database
```

### Princípios Arquiteturais

* Arquitetura desacoplada entre Frontend, Backend e Banco de Dados
* Separação clara entre visualização, simulação e persistência
* Estratégias de IA intercambiáveis via Strategy Pattern
* Design preparado para expansão modular de novos motores cognitivos

---

## 🛠 Stack Tecnológica

### Frontend

* React
* TypeScript
* @react-three/fiber
* @react-three/drei
* CSS Nativo

### Backend

* Python 3.12
* FastAPI
* Pydantic
* PyTorch

### Banco de Dados

* Neo4j (Modelagem de Grafos)

---

## 🧠 Motores de Inteligência

## 1. Q-Learning Engine

Modelo de aprendizado por reforço onde agentes buscam maximizar recompensa acumulada.

### Características

* Aprendizado por tentativa e erro
* Descoberta progressiva de obstáculos
* Sistema de recompensa e penalidade configurável
* Heatmaps de rotas aprendidas

### Objetivo

Encontrar o caminho ótimo até recursos disponíveis minimizando custo e risco.

---

## 2. Biological FSM Engine

Simulação de sobrevivência baseada em Máquina de Estados Finita com foco em comportamento biológico emergente.

### Profissões dos Agentes

* Fazendeiro
* Lenhador
* Construtor

---

## 🧬 Sistemas Biológicos

### Metabolismo

* Consumo energético passivo
* Gasto por movimentação
* Fadiga por trabalho intensivo

### Envelhecimento

* Ciclo de vida finito
* Senescência progressiva
* Morte natural probabilística

### Fome e Saúde

* Fome reduz HP quando zerada
* Agentes mortos geram loot persistente

---

## 🧬 Genética e Reprodução

### Sistema Genético

Herança procedural de:

* Cor genética (RGB/Hex)
* Traços de personalidade
* Parâmetros comportamentais

### Reprodução Controlada

Condições obrigatórias:

* Fome > 70
* Recursos mínimos disponíveis
* Parceiro válido encontrado

### Proteção Genealógica

Neo4j bloqueia relações incestuosas via análise de grafos:

* Pais/Filhos
* Irmãos
* Tios/Sobrinhos

---

## 💰 Economia Emergente

Sistema de mercado autônomo onde agentes negociam:

* Madeira
* Pedra
* Batatas
* Cercas

### Moeda Interna

**Plobs**

### Formação de Preços

Preço determinado dinamicamente por:

* Ganância individual
* Nível de fome
* Escassez de inventário

---

## 🧠 Memória Espacial

Agentes mantêm mapa mental interno de recursos conhecidos.

### Recursos Cognitivos

* Memorização de localizações úteis
* Invalidação de memórias obsoletas
* Replanejamento de rota em tempo real

---

## 📊 Observabilidade e Telemetria

### Dashboard de Simulação

* Censo populacional em tempo real
* Visualização genética por agente
* Patrimônio individual atualizado dinamicamente

### Event Log

Registro cronológico de:

* Nascimentos
* Casamentos
* Mortes
* Comércio
* Ataques

### Futuro

* Visualização completa da árvore genealógica via grafos interativos

---

## 🚀 Como Executar

## Pré-requisitos

* Node.js 18+
* Python 3.12+
* Neo4j rodando na porta 7687

**Credenciais padrão:**

```txt
Senha: admin123
```

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Backend

```bash
cd backend
python -m venv venv
```

### Ativar ambiente virtual

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### Rodar servidor

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## 📈 Roadmap Futuro

* [ ] Sistema de Predadores Inteligentes
* [ ] Climas Dinâmicos / Estações
* [ ] Catástrofes Naturais
* [ ] Religião / Cultura Emergente
* [ ] Guerra entre Facções
* [ ] Evolução Genética Complexa
* [ ] Redes Neurais por Agente

---

## 🧪 Valor Técnico do Projeto

Este projeto demonstra experiência prática em:

* Arquitetura de sistemas complexos
* Inteligência Artificial aplicada
* Machine Learning / Reinforcement Learning
* Modelagem de sistemas emergentes
* Bancos de dados em grafo
* Engenharia de software orientada a padrões
* Renderização 3D em tempo real

---

## 📄 Licença

Defina aqui sua licença de uso (MIT, Apache 2.0, Proprietária etc.)

---

## 👨‍💻 Autor

Desenvolvido por **[Alex Rosendo]**
