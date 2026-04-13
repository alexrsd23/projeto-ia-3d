import { useState, useEffect, useRef } from 'react';
import Dashboard from './components/layout/Dashboard';
import Viewport3D from './components/layout/Viewport3D';
import EventLogPanel from './components/ui/EventLogPanel';
import NeuralNetworkVisualizer from './components/ui/NeuralNetworkVisualizer';
import type { Entity, TileData, SimulationEvent, RouteAnalytics } from './types';
import './App.css';
import { CHARACTER_SETTINGS } from './config/characterSettings';
import TelemetryPanel from './components/ui/TelemetryPanel';

export default function App() {
  const [isDay, setIsDay] = useState(true);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);

  // === A MEMÓRIA DIVINA DE GERAÇÃO (Garante Homem -> Mulher -> Homem) ===
  const nextSpawnSexRef = useRef<'M' | 'F'>('M');

  const handleClearLogs = () => setEvents([]);

  const [heatmap, setHeatmap] = useState<{ gridX: number, gridZ: number, visits: number }[]>([]);
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [lastNNAction, setLastNNAction] = useState<number>(0);
  const [selectedTileId, setSelectedTileId] = useState<string | null>(null);

  const [qValues, setQValues] = useState<number[]>(Array(8).fill(0));
  const [nnState, setNNState] = useState<number[]>([0, 0, 0]);

  // MODO DE TESTE DE ROTAS
  const [isRouteTestingMode, setIsRouteTestingMode] = useState(false);
  const [routeBounds, setRouteBounds] = useState({ xMin: -24, xMax: -24, zMin: 24, zMax: 24 });

  // === NOVO: ESTADO DO MODO DE EDIÇÃO DE TERRENO ===
  const [isTerrainEditingMode, setIsTerrainEditingMode] = useState(false);

  // === NOVO: ESTADO DO VISUALIZADOR DA REDE NEURAL (Desativado por padrão) ===
  const [showNeuralNet, setShowNeuralNet] = useState(false);

  const [showNames, setShowNames] = useState(false);

  const isProcessingTick = useRef(false);

  const [analytics, setAnalytics] = useState<RouteAnalytics | null>(null);
  const [currentMode, setCurrentMode] = useState<string>('ROUTES');

  const [sunPos, setSunPos] = useState<[number, number, number]>(() => {
    const saved = localStorage.getItem('sunPos');
    return saved ? JSON.parse(saved) : [20, 30, 20];
  });
  const [moonPos, setMoonPos] = useState<[number, number, number]>(() => {
    const saved = localStorage.getItem('moonPos');
    return saved ? JSON.parse(saved) : [-20, 30, -20];
  });

  const [tiles, setTiles] = useState<TileData[]>(() => {
    const initialTiles: TileData[] = [];
    for (let x = -24; x <= 24; x += 2) {
      for (let z = -24; z <= 24; z += 2) {
        initialTiles.push({ id: `tile-${x}-${z}`, gridX: x, gridZ: z, type: 'grass', crops: [] });
      }
    }
    return initialTiles;
  });

  const saveTileToDatabase = async (tileData: TileData) => {
    try { await fetch('http://127.0.0.1:8000/api/tiles', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(tileData) }); } catch (error) { console.error(error); }
  };

  const handlePlowTile = (id: string) => {
    const tile = tiles.find(t => t.id === id);
    if (!tile) return;
    const updatedTile = { ...tile, type: 'farm' as const };
    setTiles(prev => prev.map(t => t.id === id ? updatedTile : t));
    saveTileToDatabase(updatedTile);
  };

  const handlePlantCrop = (id: string) => {
    const tile = tiles.find(t => t.id === id);
    if (!tile || tile.type !== 'farm' || tile.crops.length >= 2) return;
    const offset: [number, number] = tile.crops.length === 0 ? [-0.5, -0.5] : [0.5, 0.5];
    const newCrop = { id: crypto.randomUUID(), type: 'potato' as const, stage: 0 as const, positionOffset: offset };
    const updatedTile = { ...tile, crops: [...tile.crops, newCrop] };
    setTiles(prev => prev.map(t => t.id === id ? updatedTile : t));
    saveTileToDatabase(updatedTile);
  };

  const handleMoveSun = (pos: [number, number, number]) => { setSunPos(pos); localStorage.setItem('sunPos', JSON.stringify(pos)); };
  const handleMoveMoon = (pos: [number, number, number]) => { setMoonPos(pos); localStorage.setItem('moonPos', JSON.stringify(pos)); };

  const handleMoveEntity = async (id: string, newPos: [number, number, number]) => {
    setEntities(prev => prev.map(e => e.id === id ? { ...e, position: newPos } : e));
    try { await fetch(`http://127.0.0.1:8000/api/entities/${id}/position`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ position: newPos }) }); } catch (error) { console.error(error); }
  };

  const handleRotateEntity = async (id: string, newRotation: number) => {
    setEntities(prev => prev.map(e => e.id === id ? { ...e, rotation: newRotation } : e));
    try {
      await fetch(`http://127.0.0.1:8000/api/entities/${id}/rotate`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rotation: newRotation })
      });
    } catch (error) { console.error(error); }
  };

  const handleSaveIdentity = async (id: string, name: string, birthdate: string) => {
    setEntities(prev => prev.map(e => e.id === id ? { ...e, name, birthdate } : e));
    try { await fetch(`http://127.0.0.1:8000/api/entities/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, birthdate }) }); } catch (error) { console.error(error); }
  };

  const selectedEntity = entities.find(e => e.id === selectedEntityId);

  useEffect(() => {
    const fetchWorld = async () => {
      try {
        const resBrain = await fetch('http://127.0.0.1:8000/api/brain/mode');
        let mode = 'ROUTES';
        if (resBrain.ok) {
          const brainData = await resBrain.json();
          mode = brainData.current_mode;
          setCurrentMode(mode);
        }

        // ROTEAMENTO DINÂMICO SEGURO!
        const endpoint = mode === 'SURVIVAL' ? 'http://127.0.0.1:8000/api/entities/survival_world' : 'http://127.0.0.1:8000/api/entities';
        const resEntities = await fetch(endpoint);
        if (resEntities.ok) setEntities(await resEntities.json());

        const resTiles = await fetch('http://127.0.0.1:8000/api/tiles');
        if (resTiles.ok) {
          const savedTiles: TileData[] = await resTiles.json();
          setTiles(prev => {
            const newTiles = [...prev];
            savedTiles.forEach(savedTile => {
              const index = newTiles.findIndex(t => t.id === savedTile.id);
              if (index !== -1) newTiles[index] = savedTile;
            });
            return newTiles;
          });
        }
      } catch (error) { console.error(error); }
    };
    fetchWorld();
  }, []);

  useEffect(() => {
    let interval: number;
    if (isRunning) {
      interval = setInterval(async () => {
        if (isProcessingTick.current) return;
        isProcessingTick.current = true;
        try {
          const responseTick = await fetch('http://127.0.0.1:8000/api/tick', { method: 'POST' });
          if (responseTick.ok) {
            const tickData = await responseTick.json();
            if (tickData.analytics) setAnalytics(tickData.analytics);
            if (tickData.heatmap) setHeatmap(tickData.heatmap);
            if (tickData.lastAction !== undefined) setLastNNAction(tickData.lastAction);
            // NOVO: Lê os valores da API do Python
            if (tickData.qValues) setQValues(tickData.qValues);
            if (tickData.currentState) setNNState(tickData.currentState);
            if (tickData.events && tickData.events.length > 0) {
              const newEvents = [...tickData.events].reverse();
              setEvents(prev => [...newEvents, ...prev].slice(0, 2000));
            }
          }
          // ROTEAMENTO DINÂMICO DURANTE O TICK!
          const endpoint = currentMode === 'SURVIVAL' ? 'http://127.0.0.1:8000/api/entities/survival_world' : 'http://127.0.0.1:8000/api/entities';
          const responseEntities = await fetch(endpoint);

          if (responseEntities.ok) setEntities(await responseEntities.json());
          const responseTiles = await fetch('http://127.0.0.1:8000/api/tiles');
          if (responseTiles.ok) {
            const savedTiles: TileData[] = await responseTiles.json();
            setTiles(prev => {
              const newTiles = [...prev];
              savedTiles.forEach(savedTile => {
                const index = newTiles.findIndex(t => t.id === savedTile.id);
                if (index !== -1) newTiles[index] = savedTile;
              });
              return newTiles;
            });
          }
        } catch (error) { console.error(error); } finally { isProcessingTick.current = false; }
      }, 250);
    }
    return () => clearInterval(interval);
  }, [isRunning]);


  // ========================================================
  // SPAWN CONTROLLER REFINADO (GERAÇÃO EM MASSA E DNA)
  // ========================================================
  const handleAddEntity = async (type: string, amount: number = 1) => {
    const newEntities: Entity[] = [];
    const fetchPromises: Promise<any>[] = [];

    // Função auxiliar para o DNA visual
    const getRandomColor = () => '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');

    for (let i = 0; i < amount; i++) {
      let snapX = 0;
      let snapZ = 0;
      let validPositionFound = false;
      let attempts = 0;

      // === SISTEMA DE BIOLOGIA E GENÉTICA (GERAÇÃO 0) ===
      const isSentient = ['character', 'farmer', 'woodcutter', 'builder', 'wolf'].includes(type);
      let agentSex = 'M';
      let agentColor = '#ffffff';
      let agentProfession = 'Desempregado';
      let agentTrust = 50;
      let agentLie = 0;

      if (isSentient) {
        // Regra Divina: Alterna o sexo estritamente
        agentSex = nextSpawnSexRef.current;
        nextSpawnSexRef.current = nextSpawnSexRef.current === 'M' ? 'F' : 'M';

        agentColor = getRandomColor();
        // A natureza lhes dá personalidades caóticas de berço (0 a 100)
        agentTrust = Math.floor(Math.random() * 101);
        agentLie = Math.floor(Math.random() * 101);

        switch (type) {
          case 'farmer': agentProfession = 'Fazendeiro'; break;
          case 'woodcutter': agentProfession = 'Lenhador'; break;
          case 'builder': agentProfession = 'Construtor'; break;
          case 'character': agentProfession = 'Explorador'; break;
          case 'wolf': agentProfession = 'Lobo Selvagem'; break;
        }
      }

      // === SISTEMA DE POSICIONAMENTO INTELIGENTE (Anti-Sobreposição Universal) ===
      while (!validPositionFound && attempts < 50) {
        let rawX, rawZ;

        // 1. Gera coordenadas baseadas na regra (Área de Teste vs Mapa Inteiro)
        if (isRouteTestingMode && isSentient) {
          rawX = Math.random() * (routeBounds.xMax - routeBounds.xMin) + routeBounds.xMin;
          rawZ = Math.random() * (routeBounds.zMax - routeBounds.zMin) + routeBounds.zMin;
        } else {
          // O mapa vai de -24 a 24 (tamanho total de 48)
          rawX = (Math.random() - 0.5) * 48;
          rawZ = (Math.random() - 0.5) * 48;
        }

        // 2. Trava na grade 2x2 para alinhamento perfeito
        snapX = Math.round(rawX / 2) * 2;
        snapZ = Math.round(rawZ / 2) * 2;

        // 3. Trava de segurança para não nascer fora dos limites do mapa
        if (isRouteTestingMode && isSentient) {
          snapX = Math.max(routeBounds.xMin, Math.min(routeBounds.xMax, snapX));
          snapZ = Math.max(routeBounds.zMin, Math.min(routeBounds.zMax, snapZ));
        } else {
          snapX = Math.max(-24, Math.min(24, snapX));
          snapZ = Math.max(-24, Math.min(24, snapZ));
        }

        // 4. O RADAR MÁGICO: Pergunta ao sistema se já tem algo ali!
        // (Verifica os velhos moradores E os que estão nascendo no mesmo clique)
        const isOccupied = entities.some(e => e.position[0] === snapX && e.position[2] === snapZ) ||
          newEntities.some(e => e.position[0] === snapX && e.position[2] === snapZ);

        if (!isOccupied) {
          validPositionFound = true; // Se está livre, achamos o lugar perfeito!
        }

        attempts++;
      }

      // Se não achou espaço livre depois de 50 tentativas, pula este boneco/árvore 
      // para evitar travamentos infinitos se o mapa estiver cheio
      if (!validPositionFound) continue;

      // === AJUSTE DE GRAVIDADE (FÍSICA DE COLISÃO COM O CHÃO) ===
      let positionY = 0.5; // Padrão: Personagens e Casas (Pés tocam no -0.5)

      // O verdadeiro chão do mundo está na cota -0.5!
      // A base da natureza, muros e animais quadrúpedes precisa ser "plantada" nessa cota.
      if (['cactus', 'tree', 'stump', 'stone', 'fence', 'gate', 'damaged_fence', 'wolf'].includes(type)) {
        positionY = -0.5;
      }

      // O tronco está deitado e tem um raio de 0.15. 
      // Para ele ficar deitado na grama sem afundar: -0.5 + 0.15 = -0.35
      if (type === 'log') {
        positionY = -0.35;
      }

      const randomNameNumber = Math.floor(Math.random() * 90) + 10;

      const newEntity: Entity = {
        id: crypto.randomUUID(),
        type: type as any,
        position: [snapX, positionY, snapZ],
        rotation: 0,
        ...(isSentient && {
          name: `${agentProfession} ${randomNameNumber}`,
          health: CHARACTER_SETTINGS.defaultHealth,
          hunger: CHARACTER_SETTINGS.defaultHunger,
          // === INJETANDO O DNA NO BANCO DE DADOS ===
          color: agentColor,
          sex: agentSex as 'M' | 'F',
          profession: agentProfession,
          trustLevel: agentTrust,
          lieLevel: agentLie,
          // === A MÃO DE DEUS INJETA O CAPITAL INICIAL E A RAM AQUI ===
          inventoryJSON: JSON.stringify({ plobs: 50.0, potatoes: 0, seeds: 0, logs: 0, stones: 0, fences: 0 }),
          memoryJSON: JSON.stringify({ food: {}, farms: {}, hazards: {} }),
          state: "IDLE"
        })
      };

      newEntities.push(newEntity);

      // Desvia o endpoint baseado na profissão para gravar as sub-tabelas corretas no Neo4j
      let endpoint = 'http://127.0.0.1:8000/api/entities';
      if (['farmer', 'woodcutter', 'builder', 'wolf'].includes(type)) {
        endpoint = `http://127.0.0.1:8000/api/entities/${type}`;
      }

      fetchPromises.push(
        fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newEntity),
        })
      );
    }

    setEntities((prev) => [...prev, ...newEntities]);

    try {
      await Promise.all(fetchPromises);
    } catch (error) {
      console.error("Erro ao gerar entidades em massa:", error);
    }
  };

  // ========================================================
  // SISTEMA DE EXPURGO (MATA AGENTES MAS MANTÉM IA)
  // ========================================================
  const handleKillAllAgents = async () => {
    // 1. Limpa os agentes E animais da tela instantaneamente
    setEntities(prev => prev.filter(e => !['character', 'farmer', 'woodcutter', 'builder', 'wolf'].includes(e.type)));

    // 2. Se o utilizador estava com um agente selecionado, desmarca-o
    if (['character', 'farmer', 'woodcutter', 'builder', 'wolf'].includes(selectedEntity?.type || '')) {
      setSelectedEntityId(null);
    }

    // 3. Pede ao Python para apagar do Neo4j
    try {
      await fetch('http://127.0.0.1:8000/api/kill-agents', { method: 'POST' });
    } catch (error) {
      console.error("Erro ao executar expurgo:", error);
    }
  };

  // ========================================================
  // SISTEMA DE AMNÉSIA (LIMPA APENAS A RAM DA IA)
  // ========================================================
  const handleClearAIMemory = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/clear-ai-memory', { method: 'POST' });
      // Limpa os dados visuais do React instantaneamente para melhor feedback visual
      setAnalytics(null);
      setHeatmap([]);
    } catch (error) {
      console.error("Erro ao limpar memória da IA:", error);
    }
  };

  // ========================================================
  // NOVO: TROCA DE MÓDULO NEURAL (STRATEGY PATTERN)
  // ========================================================
  const handleSwitchMode = async (mode: string) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/brain/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      if (response.ok) {
        const data = await response.json();
        setCurrentMode(data.current_mode);
        // Limpa os dados visuais antigos na tela quando troca a fita
        setAnalytics(null);
        setHeatmap([]);
      }
    } catch (error) {
      console.error("Erro ao trocar o modo do cérebro:", error);
    }
  };

  // === NOVO: FUNÇÃO PARA ALTERNAR O MODO ===
  const handleToggleTerrainEditing = () => {
    setIsTerrainEditingMode(!isTerrainEditingMode);
    // Se estivermos desligando o modo, desmarca qualquer terreno que esteja selecionado
    if (isTerrainEditingMode) {
      setSelectedTileId(null);
    }
  };

  return (
    <div className="app-container">
      <Dashboard
        onAddEntity={handleAddEntity as any}
        isRunning={isRunning}
        onToggleSimulation={() => setIsRunning(!isRunning)}
        selectedEntity={selectedEntity}
        onSaveIdentity={handleSaveIdentity}
        isDay={isDay}
        onToggleDayNight={() => setIsDay(!isDay)}
        selectedTile={tiles.find(t => t.id === selectedTileId)}
        onPlow={handlePlowTile}
        onPlant={handlePlantCrop}
        onDeselectTile={() => setSelectedTileId(null)}
        isRouteTestingMode={isRouteTestingMode}
        onToggleRouteTesting={() => setIsRouteTestingMode(!isRouteTestingMode)}
        routeBounds={routeBounds}
        setRouteBounds={setRouteBounds}
        onKillAllAgents={handleKillAllAgents}
        onClearAIMemory={handleClearAIMemory}
        showNames={showNames} // LIGA NO DASHBOARD
        onToggleShowNames={() => setShowNames(!showNames)}
        currentMode={currentMode}
        onSwitchMode={handleSwitchMode}
        onClearLogs={handleClearLogs}
        isTerrainEditingMode={isTerrainEditingMode}
        onToggleTerrainEditing={handleToggleTerrainEditing}
        showNeuralNet={showNeuralNet}
        onToggleNeuralNet={() => setShowNeuralNet(!showNeuralNet)}
      />

      <div style={{ position: 'relative', flexGrow: 1 }}>
        {showNeuralNet && (
          <NeuralNetworkVisualizer lastAction={lastNNAction} qValues={qValues} state={nnState} />
        )}
        <Viewport3D
          entities={entities}
          selectedEntityId={selectedEntityId}
          onSelectEntity={(id) => setSelectedEntityId(id)}
          onDeselect={() => setSelectedEntityId(null)}
          onMoveEntity={handleMoveEntity}
          sunPos={sunPos}
          moonPos={moonPos}
          onMoveSun={handleMoveSun}
          onMoveMoon={handleMoveMoon}
          isDay={isDay}
          tiles={tiles}
          selectedTileId={selectedTileId}
          onSelectTile={(id) => setSelectedTileId(id)}
          heatmap={heatmap}
          isRouteTestingMode={isRouteTestingMode}
          routeBounds={routeBounds}
          analytics={analytics}
          showNames={showNames}
          onRotateEntity={handleRotateEntity}
          isTerrainEditingMode={isTerrainEditingMode}
        />
      </div>

      <TelemetryPanel events={events} analytics={analytics} currentMode={currentMode} />
    </div>
  );
}