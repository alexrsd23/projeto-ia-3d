# 🌍 Mundo IA - Simulador de Ecossistema e Inteligência Artificial 3D

Um ambiente de simulação 3D altamente modular projetado para estudar Inteligência Artificial, Aprendizado de Máquina (Machine Learning) e Comportamentos Emergentes em sistemas multiagentes. 

O projeto divide-se em dois "Cérebros" completamente isolados, permitindo contrastar a **Otimização Matemática Pura (Q-Learning)** com a **Autopreservação Biológica (Máquina de Estados Finita)** num mesmo mundo virtual.

---

## 🛠 Tecnologias e Arquitetura

O projeto adota uma arquitetura estritamente desacoplada (Frontend, Backend e Banco de Dados):

* **Frontend:** React, TypeScript, `@react-three/fiber` e `@react-three/drei` (Renderização 3D), CSS nativo para UI/Dashboards.
* **Backend:** Python 3.12, FastAPI (Roteamento assíncrono), Pydantic (Validação de Dados), PyTorch (Redes Neurais).
* **Banco de Dados:** Neo4j (Banco de dados orientado a grafos para mapear entidades e relações espaciais).
* **Design Pattern:** *Strategy Pattern* utilizado no `BrainManager` para alternar fluidamente entre os motores de inteligência sem poluição de código.

---

## 🧠 Modos de Simulação

O simulador opera em duas frentes independentes que podem ser alternadas em tempo real via Terminal de Controle.

### 📍 Modo 1: Otimização de Rotas (Q-Learning)
Neste modo, os agentes operam como funções matemáticas que buscam maximizar recompensas através de tentativa e erro. Eles são "oniscientes" em relação ao mapa, mas não conhecem os obstáculos até colidirem com eles.

* **Objetivo:** Encontrar o caminho mais curto e seguro até o recurso (Batata).
* **Mecânicas:**
  * **Sistema de Recompensas:** Bônus por se aproximar do alvo, punição severa por colidir com cactos ou cair do mapa, punição por exaustão (loops infinitos).
  * **Episódios e Épocas:** Cada tentativa gera dados telemétricos. Os agentes morrem ao falhar, e a IA global (Mente Colmeia) ajusta os pesos da Rede Neural.
  * **Análise Visual:** Geração de *Heatmaps* (Mapas de Calor) no chão 3D para indicar rotas frequentes e renderização das sinapses da rede neural em tempo real.

### 🛡️ Modo 2: Sobrevivência e Ecossistema (Biological FSM)
Neste modo, os agentes deixam de ser oniscientes e tornam-se organismos biológicos limitados (Fazendeiros). O foco muda de "otimizar uma rota" para "garantir a sobrevivência a longo prazo" gerando comportamento emergente descentralizado.

* **Fisiologia e Metabolismo (`biology.py`):**
  * O relógio biológico é assíncrono ao relógio físico. A fome decai gradualmente.
  * **Custo Dinâmico:** Ficar parado gasta energia mínima; andar gasta energia moderada; trabalhar a terra (arar/plantar) gera fadiga acelerada.
  * **Morte por Inanição:** Se a fome chegar a zero, a vida (HP) começa a ser drenada até a morte permanente da entidade no banco de dados.

* **Percepção e Radar (`perception.py`):**
  * Os agentes sofrem de "miopia". Eles só tomam decisões baseadas no que está dentro do seu raio de visão (ex: 15 blocos).
  * O radar filtra a natureza: distingue terras brutas, terras aráveis livres, plantas em crescimento (intocáveis) e plantas maduras (prontas para colheita).

* **Memória Espacial - O Hipocampo (`memory_system.py`):**
  * Ao explorar, os agentes mapeiam recursos mentalmente e avaliam a "Confiabilidade" daquela memória versus a distância do alvo.
  * **Amnésia Estratégica (Desassociação):** Se um agente viaja até uma terra lembrada e descobre que ela foi colhida (ou ocupada) pela concorrência, ele invalida aquela memória mentalmente para evitar *loops* e acampamentos infinitos.

* **Gestão de Inventário (`inventory.py`):**
  * Os fazendeiros possuem mochilas com capacidade limitada (ex: 4 Batatas, 4 Sementes).
  * A colheita de uma planta madura rende 1 alimento e 2 sementes, permitindo a propagação infinita do ecossistema se houver esforço de replantio.

* **Tomada de Decisão (Córtex Frontal):**
  A IA avalia as variáveis acima e enquadra-se num Estado Psicológico:
  1. `SNACKING` (Auto-regulação): Fome moderada + Comida no bolso. Come preventivamente para não parar de trabalhar.
  2. `SEEK_FOOD` (Urgência): Fome alta. Segue o radar ou a memória até ao alimento mais próximo.
  3. `FARMER` (Expansão): Saciado + Sementes no bolso. Busca terras aradas vazias para plantar ou ara mato virgem. Expande a fazenda.
  4. `STOCKPILING` (Prevenção): Passa por comida madura e tem espaço na mochila, colhendo para o futuro sem consumir.
  5. `EXPLORE` (Passeio): Sem tarefas críticas, vaga para mapear novas áreas.

---

## 📊 Telemetria e Observabilidade

O sistema conta com um **Terminal de Telemetria** avançado no Frontend para auditoria científica do comportamento:

* **Caixa-Preta de Sobrevivência (Auditoria Biológica):** Um console estilo terminal que registra cada microdecisão cronológica dos agentes (ex: *10:14:22 — Fazendeiro 12 - Conflito de espaço em X:-6 Z:2. Memória apagada. Buscando alternativas.*)
* **Live Dashboards:** Painéis flutuantes (Cards) que inspecionam o "cérebro" de um agente em tempo real ao clicar nele no mundo 3D (exibindo HP, Fome, Livro de Memórias e Inventário).
* **Ranking e Rotas:** No modo Q-Learning, o sistema cataloga as rotas de ouro (mais rápidas) e os agentes com maior taxa de sucesso.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Node.js (v18+)
* Python (3.12+)
* Banco de Dados Neo4j (Rodando localmente ou via Docker na porta padrão 7687)

### Inicializando o Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

### Inicializando o Backend (Python)

```bash
cd backend
python -m venv venv

# Ative o ambiente virtual:
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
