# Mundo IA — Simulador 3D de Ecossistema e Inteligência Artificial Multiagente

> Plataforma avançada de simulação 3D para estudo de Inteligência Artificial, comportamentos emergentes e sistemas sociais complexos em ambientes multiagentes.

---

## Visão Geral

O **Mundo IA** é um ambiente de simulação 3D modular onde agentes autônomos vivem, trabalham, reproduzem, negociam e evoluem em um mundo interativo. Toda a complexidade social — mercados, famílias, propriedade, predação — emerge organicamente das regras locais de cada agente.

O projeto implementa dois motores cognitivos independentes:

- **Q-Learning** — Agentes orientados por otimização matemática e maximização de recompensa via rede neural (PyTorch).
- **Biological FSM** — Agentes orientados por sobrevivência, genética, economia e comportamento social.

Essa arquitetura permite comparar como diferentes modelos de tomada de decisão impactam a adaptação e a emergência comportamental em populações artificiais.

---

## Objetivos do Projeto

- Estudar comportamento emergente em sistemas multiagentes.
- Comparar aprendizado por reforço com máquinas de estado biológicas.
- Simular economia, genética, reprodução e mortalidade em ecossistemas artificiais.
- Criar uma base experimental para pesquisas em IA adaptativa.

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 · TypeScript 6 · Three.js · React Three Fiber · Drei |
| Backend | Python 3.12 · FastAPI · Pydantic |
| Banco de dados | Neo4j (grafo de entidades e relações) |
| IA / ML | PyTorch (Q-Learning) · FSM (máquina de estados finitos) |
| Visualização | React Flow · Dagre (árvore genealógica) |
| Build | Vite 8 |

---

## Arquitetura do Sistema

```
Frontend (React + Three.js)
        ↓ REST API (250ms polling)
Backend API (FastAPI)
        ↓
Simulation Engine (Python)
        ↓
Neo4j Graph Database
```

### Princípios Arquiteturais

- Arquitetura desacoplada entre Frontend, Backend e Banco de Dados.
- Separação clara entre visualização, simulação e persistência.
- Estratégias de IA intercambiáveis via Strategy Pattern (`brain_manager.py`).
- Design preparado para expansão modular de novos motores cognitivos.

### Fluxo de Tick

A cada 250ms, enquanto a simulação está ativa:

```
POST /api/tick
  → Backend processa um tick completo
  → Cada agente: percebe → decide → age → atualiza memória
  → Retorna: posições, eventos, analytics, heatmap

React atualiza estado → Three.js re-renderiza a cena 3D
```

---

## Modos de Simulação

### Modo ROUTES — Q-Learning

Agente único que aprende rotas ótimas para recursos via Q-Learning com rede neural PyTorch.

- Aprendizado por tentativa e erro com sistema de recompensa e penalidade configurável.
- Descoberta progressiva de obstáculos e caminhos.
- Heatmap de exploração e visualização de Q-values em tempo real.
- Objetivo: encontrar o caminho ótimo até recursos minimizando custo e risco.

### Modo SURVIVAL — Sociedade Emergente

Modo principal. Múltiplos agentes com profissões, metabolismo, economia, reprodução e morte real.

---

## Sistemas do Modo Survival

### Biologia e Metabolismo

- Consumo de energia variável por tipo de ação: descanso, movimento, trabalho intensivo.
- Fome progressiva (0–100%): ao atingir o limite, o agente perde HP e morre por inanição.
- Envelhecimento ao longo de ~2500 ticks de simulação com morte natural.
- Agentes mortos geram **loot** (inventário dropado) coletável por sobreviventes.

### Genética e Reprodução

- DNA misturado na reprodução: filhos herdam cor (RGB), traços de personalidade e tendência de profissão.
- Reprodução baseada em sexo (macho/fêmea) com condições obrigatórias: fome > 70, recursos mínimos, parceiro válido.
- **Proteção genealógica via Neo4j**: pais/filhos, irmãos e tios/sobrinhos são bloqueados automaticamente.
- Filhos herdam capital, inventário e propriedades dos pais.

### Profissões

| Profissão | Função Principal |
|-----------|-----------------|
| Farmer | Cultiva batatas, planta árvores, ara a terra |
| Woodcutter | Corta árvores, coleta toras, comércio de madeira em bulk |
| Builder | Constrói cercas e portões, cumpre contratos, repara estruturas |
| Blacksmith | Forja peças metálicas, repara ferramentas, cria sementes |
| Wolf | Predador NPC que caça os outros agentes |

### Economia Emergente

- **Moeda interna:** Plobs.
- **Bens negociáveis:** batatas, toras, pedras, cercas, portões, peças metálicas, sementes de árvore.
- **Preços dinâmicos** calculados em função de escassez de inventário, nível de fome e personalidade (ganância).
- Negociação com diálogo real: confiança, possibilidade de mentira e contra-ofertas.
- **Sistema de boicote:** agentes memorizam parceiros de mau negócio e os evitam.
- **Contratos de construção:** builders recebem e executam pedidos de clientes com rastreamento de pagamento.

### Agricultura e Propriedade

- Agentes reservam e reivindicam plots de terra com direito de propriedade verificado por coordenada.
- **Herança de terra:** cônjuge → filhos → abandono (usucapião implementada).
- Cultivo de batatas em 3 estágios: semente → crescendo → maduro.
- Apodrecimento de colheita e entropia de estruturas (cercas danificam-se com o tempo).
- Máximo de 2 colheitas por tile.

### Ferramenta e Degradação

- Ferramentas de farmers, woodcutters e builders têm durabilidade (100 HP).
- Ferramentas desgastadas precisam ser reparadas pelo blacksmith (requer peças metálicas).

### Memória e Percepção

- **Radar de percepção** com alcance de 15 unidades: detecta recursos, agentes e terreno.
- **Memória espacial:** cache de localização de alimentos, fazendas, perigos e agentes hostis.
- Invalidação de memórias obsoletas e replanejamento de rota em tempo real.
- Listas de boicote e zonas de rejeição persistem entre ticks.

### Família e Genealogia

- Casamento, filhos e rastreamento completo de árvore genealógica no Neo4j.
- Relações armazenadas como grafo: `:MARRIED_TO`, `:PARENT_OF`, `:OWNS`.
- Visualização interativa da árvore familiar no frontend via React Flow.

---

## Observabilidade e Telemetria

### Dashboard

- Censo populacional em tempo real.
- Visualização genética (cor herdada) por agente.
- Patrimônio e inventário individuais atualizados dinamicamente.
- Heatmap de rotas (modo ROUTES) e Q-values por ação.

### Event Log

Registro cronológico de todos os eventos da simulação:
- Nascimentos, casamentos e mortes.
- Comércio, contratos e quebra de acordo.
- Ataques de predadores.
- Scarcity alerts de mercado.

---

## Estrutura de Arquivos

```
projeto-ia-3d/
├── src/
│   ├── App.tsx                            # Orquestrador principal, loop de polling
│   ├── types.ts                           # Interfaces TypeScript globais
│   └── components/
│       ├── 3d/                            # Modelos 3D (personagens, ambiente)
│       │   ├── Character.tsx
│       │   ├── AdvancedCharacter.tsx
│       │   ├── House.tsx
│       │   └── environment/               # Tree, Stone, Wolf, Fence, construções
│       ├── layout/
│       │   ├── Dashboard.tsx              # Painel de controle da simulação
│       │   └── Viewport3D.tsx             # Canvas 3D (câmera, cena, iluminação)
│       └── ui/
│           ├── EventLogPanel.tsx          # Stream de eventos em tempo real
│           ├── TelemetryPanel.tsx         # Estatísticas da simulação
│           ├── InventoryCard.tsx          # Inventário do agente selecionado
│           ├── CharacterInfoCard.tsx      # Informações detalhadas do agente
│           └── NeuralNetworkVisualizer    # Visualização de Q-values
├── backend/
│   ├── main.py                            # Entrada FastAPI, CORS, roteadores
│   ├── models.py                          # Schemas Pydantic
│   ├── database.py                        # Conexão Neo4j
│   ├── ai_navigation.py                   # Q-Learning, heatmap, analytics de rotas
│   ├── brain_manager.py                   # Alternância ROUTES ↔ SURVIVAL
│   ├── routers/
│   │   ├── interactions.py                # CRUD de entidades
│   │   ├── simulation_routes.py           # Tick, spawn, heatmap
│   │   ├── brain_control.py               # Troca de modo, reset de IA
│   │   ├── family_routes.py               # Casamento, genealogia
│   │   └── farming.py                     # Tiles, colheitas, terra arável
│   └── survival/
│       ├── survival_engine.py             # Loop de tick principal (~1100 linhas)
│       ├── survival_brain.py              # IA de decisão dos agentes (~1900 linhas)
│       ├── biology.py                     # Metabolismo, envelhecimento, DNA, reprodução
│       ├── economy_system.py              # Precificação, negociação, trades
│       ├── inventory.py                   # Itens, capacidade, receitas de craft
│       ├── memory_system.py               # Memória espacial e persistência
│       ├── perception.py                  # Radar de percepção ambiental
│       ├── farm_planner.py                # Planejamento agrícola
│       ├── forestry_system.py             # Corte de árvores e coleta de toras
│       └── market_intelligence.py         # Análise de preços e mercado
└── package.json
```

---

## Como Executar

### Pré-requisitos

- Node.js 18+
- Python 3.12+
- Neo4j rodando na porta 7687

**Credenciais padrão do Neo4j:**
```
Senha: admin123
```

### Frontend

```bash
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv venv
```

Ativar ambiente virtual:

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

Instalar dependências e rodar:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## Fenômenos Emergentes Observados

- Mercados se auto-regulam via rastreamento de escassez e boicotes.
- Herança cria dinastias de riqueza entre gerações.
- Casamento forma unidades econômicas cooperativas.
- Lobos moldam o comportamento de fuga e percepção de perigo dos demais agentes.
- Rotas aprendidas via Q-Learning se otimizam progressivamente com o tempo.

---

## Roadmap

- [ ] IA expandida para predadores (lobos com aprendizado)
- [ ] Climas e estações dinâmicas
- [ ] Catástrofes naturais
- [ ] Religião e cultura emergentes
- [ ] Guerra entre facções
- [ ] Evolução genética avançada por seleção natural
- [ ] Redes neurais individuais por agente

---

## Valor Técnico

Este projeto demonstra experiência prática em:

- Arquitetura de sistemas complexos (Strategy Pattern, REST desacoplado)
- Inteligência Artificial aplicada: Q-Learning, FSM, pathfinding A*
- Machine Learning / Reinforcement Learning com PyTorch
- Modelagem de sistemas emergentes e auto-organização
- Bancos de dados em grafo (Neo4j)
- Renderização 3D em tempo real com Three.js e React Three Fiber
- Simulação de economia, genética e comportamento social

---

## Licença

Defina aqui sua licença de uso (MIT, Apache 2.0, Proprietária etc.)

---

## Autor

Desenvolvido por **Alex Rosendo**
