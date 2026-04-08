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
  
  const [heatmap, setHeatmap] = useState<{ gridX: number, gridZ: number, visits: number }[]>([]);
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [lastNNAction, setLastNNAction] = useState<number>(0);
  const [selectedTileId, setSelectedTileId] = useState<string | null>(null);

  const [qValues, setQValues] = useState<number[]>(Array(8).fill(0));
  const [nnState, setNNState] = useState<number[]>([0,0,0]);

  // MODO DE TESTE DE ROTAS
  const [isRouteTestingMode, setIsRouteTestingMode] = useState(true);
  const [routeBounds, setRouteBounds] = useState({ xMin: -24, xMax: -24, zMin: 24, zMax: 24 });

  const [showNames, setShowNames] = useState(false);

  const isProcessingTick = useRef(false);

  const [analytics, setAnalytics] = useState<RouteAnalytics | null>(null);

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

  const handleSaveIdentity = async (id: string, name: string, birthdate: string) => {
    setEntities(prev => prev.map(e => e.id === id ? { ...e, name, birthdate } : e));
    try { await fetch(`http://127.0.0.1:8000/api/entities/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, birthdate }) }); } catch (error) { console.error(error); }
  };

  const selectedEntity = entities.find(e => e.id === selectedEntityId);

  useEffect(() => {
    const fetchWorld = async () => {
      try {
        const resEntities = await fetch('http://127.0.0.1:8000/api/entities');
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
              setEvents(prev => [...tickData.events, ...prev].slice(0, 2000));
            }
          }
          const responseEntities = await fetch('http://127.0.0.1:8000/api/entities');
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
  // SPAWN CONTROLLER REFINADO (GERAÇÃO EM MASSA)
  // ========================================================
  const handleAddEntity = async (type: 'house' | 'character' | 'cactus', amount: number = 1) => {
    const newEntities: Entity[] = [];
    const fetchPromises: Promise<any>[] = [];

    // Repete a lógica de nascimento 'amount' vezes
    for (let i = 0; i < amount; i++) {
      let snapX = 0;
      let snapZ = 0;
      let validPositionFound = false;
      let attempts = 0;

      if (isRouteTestingMode && type === 'character') {
        while (!validPositionFound && attempts < 50) {
          const rawX = Math.random() * (routeBounds.xMax - routeBounds.xMin) + routeBounds.xMin;
          const rawZ = Math.random() * (routeBounds.zMax - routeBounds.zMin) + routeBounds.zMin;
          
          snapX = Math.round(rawX / 2) * 2;
          snapZ = Math.round(rawZ / 2) * 2;
          snapX = Math.max(routeBounds.xMin, Math.min(routeBounds.xMax, snapX));
          snapZ = Math.max(routeBounds.zMin, Math.min(routeBounds.zMax, snapZ));

          // Validador: Olha para os que já existem E para os que acabaram de ser gerados neste loop
          const isOccupied = entities.some(e => e.position[0] === snapX && e.position[2] === snapZ) ||
                             newEntities.some(e => e.position[0] === snapX && e.position[2] === snapZ);
          
          if (!isOccupied) validPositionFound = true;
          attempts++;
        }
      } 
      else {
        const rawX = (Math.random() - 0.5) * 20;
        const rawZ = (Math.random() - 0.5) * 20;
        snapX = Math.round(rawX / 2) * 2;
        snapZ = Math.round(rawZ / 2) * 2;
      }

      const positionY = type === 'house' ? 0.5 : (type === 'cactus' ? -0.5 : 0.5);
      const randomNameNumber = Math.floor(Math.random() * 90) + 10;

      const newEntity: Entity = {
        id: crypto.randomUUID(),
        type: type,
        position: [snapX, positionY, snapZ],
        ...(type === 'character' && {
          name: `Agente ${randomNameNumber}`,
          health: CHARACTER_SETTINGS.defaultHealth,
          hunger: CHARACTER_SETTINGS.defaultHunger,
        })
      };

      newEntities.push(newEntity);

      // Prepara o disparo para o banco de dados
      fetchPromises.push(
        fetch('http://127.0.0.1:8000/api/entities', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newEntity),
        })
      );
    }

    // Coloca todos na tela de uma vez só!
    setEntities((prev) => [...prev, ...newEntities]);

    // Envia todos para o Neo4j simultaneamente (Promise.all é muito mais rápido que esperar um a um)
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
    // 1. Limpa os agentes da tela instantaneamente (mantém casas e cactos)
    setEntities(prev => prev.filter(e => e.type !== 'character'));
    
    // 2. Se o utilizador estava com um agente selecionado, desmarca-o
    if (selectedEntity?.type === 'character') {
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
        onToggleShowNames={() => setShowNames(!showNames)} // FUNÇÃO QUE VIRA A CHAVE
      />

      <div style={{ position: 'relative', flexGrow: 1 }}>
        <NeuralNetworkVisualizer lastAction={lastNNAction} qValues={qValues} state={nnState} />
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
          showNames={showNames} // LIGA NO VIEWPORT
        />
      </div>

      <TelemetryPanel events={events} analytics={analytics} />
    </div>
  );
}