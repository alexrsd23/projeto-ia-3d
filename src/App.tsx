import { useState, useEffect } from 'react';
import Dashboard from './components/layout/Dashboard';
import Viewport3D from './components/layout/Viewport3D';
import { type Entity } from './types';
import './App.css';

export default function App() {
  const [isDay, setIsDay] = useState(true);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  // Inicia lendo a memória do navegador. Se não tiver nada, usa a posição padrão.
  const [sunPos, setSunPos] = useState<[number, number, number]>(() => {
    const saved = localStorage.getItem('sunPos');
    return saved ? JSON.parse(saved) : [20, 30, 20];
  });
  
  const [moonPos, setMoonPos] = useState<[number, number, number]>(() => {
    const saved = localStorage.getItem('moonPos');
    return saved ? JSON.parse(saved) : [-20, 30, -20];
  });

  // Funções que atualizam a tela e já salvam na memória do navegador ao mesmo tempo
  const handleMoveSun = (pos: [number, number, number]) => {
    setSunPos(pos);
    localStorage.setItem('sunPos', JSON.stringify(pos));
  };

  const handleMoveMoon = (pos: [number, number, number]) => {
    setMoonPos(pos);
    localStorage.setItem('moonPos', JSON.stringify(pos));
  };

  // Nova função para salvar o movimento no banco de dados!
  const handleMoveEntity = async (id: string, newPos: [number, number, number]) => {
    // Atualiza a tela instantaneamente
    setEntities(prev => prev.map(e => e.id === id ? { ...e, position: newPos } : e));

    // Salva no Neo4j
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/entities/${id}/position`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: newPos })
      });
      
      if (response.ok) {
        console.log(`✅ Posição salva no banco de dados!`);
      } else {
        console.error("❌ O backend recusou o salvamento:", await response.text());
      }
    } catch (error) {
      console.error("❌ Erro de conexão com o Python:", error);
    }
  };

  // Nova função para salvar no backend
  const handleSaveIdentity = async (id: string, name: string, birthdate: string) => {
    // 1. Atualiza na tela instantaneamente
    setEntities(prev => prev.map(e => 
      e.id === id ? { ...e, name, birthdate } : e
    ));

    // 2. Manda pro Neo4j
    try {
      await fetch(`http://127.0.0.1:8000/api/entities/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, birthdate })
      });
    } catch (error) {
      console.error("Erro ao salvar identidade:", error);
    }
  };

  const selectedEntity = entities.find(e => e.id === selectedEntityId);

  // Carrega o mundo inicial
  useEffect(() => {
    const fetchWorld = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/entities');
        if (response.ok) {
          const data = await response.json();
          setEntities(data);
        }
      } catch (error) {
        console.error("Erro ao carregar o mundo:", error);
      }
    };
    fetchWorld();
  }, []);

  // O "Game Loop" - Roda a cada 1 segundo se a simulação estiver ligada
  useEffect(() => {
    let interval: number;

    if (isRunning) {
      interval = setInterval(async () => {
        try {
          // 1. Manda o backend calcular o próximo passo
          await fetch('http://127.0.0.1:8000/api/tick', { method: 'POST' });
          
          // 2. Pega as novas posições e atualiza o 3D
          const response = await fetch('http://127.0.0.1:8000/api/entities');
          if (response.ok) {
            const data = await response.json();
            setEntities(data);
          }
        } catch (error) {
          console.error("Erro no Tick de simulação:", error);
        }
      }, 1000); // 1000 ms = 1 segundo
    }

    return () => clearInterval(interval);
  }, [isRunning]);

  // Função de Adicionar
  const handleAddEntity = async (type: 'house' | 'character') => {
    const randomX = (Math.random() - 0.5) * 10;
    const randomZ = (Math.random() - 0.5) * 10;
    const positionY = type === 'house' ? 0.5 : 0.5;

    const newEntity: Entity = {
      id: crypto.randomUUID(),
      type: type,
      position: [randomX, positionY, randomZ]
    };

    setEntities((prev) => [...prev, newEntity]);

    try {
      await fetch('http://127.0.0.1:8000/api/entities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEntity),
      });
    } catch (error) {
      console.error("Erro ao salvar:", error);
    }
  };

  return (
    <div className="app-container">
      <Dashboard 
        onAddEntity={handleAddEntity} 
        isRunning={isRunning}
        onToggleSimulation={() => setIsRunning(!isRunning)}
        selectedEntity={selectedEntity}
        onSaveIdentity={handleSaveIdentity}
        isDay={isDay}
        onToggleDayNight={() => setIsDay(!isDay)}
      />
      
     <Viewport3D 
        entities={entities} 
        selectedEntityId={selectedEntityId}
        onSelectEntity={(id) => setSelectedEntityId(id)}
        onDeselect={() => setSelectedEntityId(null)}
        onMoveEntity={handleMoveEntity}
        sunPos={sunPos}
        onMoveSun={setSunPos}
        moonPos={moonPos}
        onMoveMoon={setMoonPos}
        isDay={isDay} 
      />
    </div>
  );
}