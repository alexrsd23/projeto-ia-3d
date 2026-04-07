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

  // MODO DE TESTE DE ROTAS
  const [isRouteTestingMode, setIsRouteTestingMode] = useState(false);
  const [routeBounds, setRouteBounds] = useState({ xMin: -24, xMax: -16, zMin: 16, zMax: 24 });

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
            if (tickData.events && tickData.events.length > 0) {
              setEvents(prev => [...tickData.events, ...prev].slice(0, 20));
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
  // SPAWN CONTROLLER REFINADO (COM VALIDADOR DE ESPAÇO)
  // ========================================================
  const handleAddEntity = async (type: 'house' | 'character' | 'cactus') => {
    let snapX = 0;
    let snapZ = 0;
    let validPositionFound = false;
    let attempts = 0;

    // Se for o Modo Teste, garante que nasce dentro dos Bounds e em célula vazia
    if (isRouteTestingMode && type === 'character') {
      while (!validPositionFound && attempts < 50) {
        const rawX = Math.random() * (routeBounds.xMax - routeBounds.xMin) + routeBounds.xMin;
        const rawZ = Math.random() * (routeBounds.zMax - routeBounds.zMin) + routeBounds.zMin;
        
        // Alinhamento exato na grid
        snapX = Math.round(rawX / 2) * 2;
        snapZ = Math.round(rawZ / 2) * 2;
        
        // Clamp de segurança
        snapX = Math.max(routeBounds.xMin, Math.min(routeBounds.xMax, snapX));
        snapZ = Math.max(routeBounds.zMin, Math.min(routeBounds.zMax, snapZ));

        // Validador: Verifica se já tem alguém ou obstáculo naquela coordenada exata
        const isOccupied = entities.some(e => e.position[0] === snapX && e.position[2] === snapZ);
        if (!isOccupied) {
          validPositionFound = true;
        }
        attempts++;
      }
    } 
    // Comportamento normal
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

    setEntities((prev) => [...prev, newEntity]);

    try {
      await fetch('http://127.0.0.1:8000/api/entities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEntity),
      });
    } catch (error) { console.error(error); }
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
      />

      <div style={{ position: 'relative', flexGrow: 1 }}>
        <NeuralNetworkVisualizer lastAction={lastNNAction} />
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
        />
      </div>

      <TelemetryPanel events={events} analytics={analytics} />
    </div>
  );
}