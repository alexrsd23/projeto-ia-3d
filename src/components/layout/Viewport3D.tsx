import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import House from '../3d/House';
import Character from '../3d/Character';
import Skybox from '../3d/environment/Skybox';
import Sun from '../3d/environment/Sun';
import Moon from '../3d/environment/Moon';
import DarknessOverlay from '../3d/environment/DarknessOverlay';
import Ground from '../3d/environment/ground/Ground';
import HeatmapSystem from '../3d/environment/ground/HeatmapSystem';
import CactusObstacle from '../3d/environment/CactusObstacle';
import SpawnAreaVisualizer from '../3d/environment/SpawnAreaVisualizer'; // O Novo Import!
import type { Entity, TileData } from '../../types';

interface RouteBounds {
  xMin: number; xMax: number; zMin: number; zMax: number;
}

interface Viewport3DProps {
  entities: any[];
  selectedEntityId: string | null;
  onSelectEntity: (id: string) => void;
  onDeselect: () => void;
  onMoveEntity: (id: string, pos: [number, number, number]) => void;
  sunPos: [number, number, number];
  moonPos: [number, number, number];
  onMoveSun: (pos: [number, number, number]) => void;
  onMoveMoon: (pos: [number, number, number]) => void;
  isDay: boolean;
  tiles: TileData[];
  selectedTileId: string | null;
  onSelectTile: (id: string) => void;
  heatmap: {gridX: number, gridZ: number, visits: number}[]; 
  
  // Nossas novas props
  isRouteTestingMode: boolean;
  routeBounds: RouteBounds;
}

export default function Viewport3D({
  entities, selectedEntityId, onSelectEntity, onDeselect, onMoveEntity,
  sunPos, moonPos, onMoveSun, onMoveMoon, isDay, tiles, selectedTileId, onSelectTile, heatmap,
  isRouteTestingMode, routeBounds
}: Viewport3DProps) {

  const [isDragging, setIsDragging] = useState(false);
  const maxVisits = heatmap && heatmap.length > 0 ? Math.max(...heatmap.map(h => h.visits)) : 0;

  return (
    <div className="viewport">
      <Canvas shadows camera={{ position: [0, 10, 20], fov: 50 }} onPointerMissed={onDeselect}>
        <color attach="background" args={[isDay ? "#b0c0c6" : "#393f48"]} />
        <OrbitControls makeDefault enabled={!isDragging} />

        <Skybox isDay={isDay} />
        <DarknessOverlay isDay={isDay} />

        {isDay ? (
          <Sun position={sunPos} isSelected={selectedEntityId === 'sun'} onClick={() => onSelectEntity('sun')} onMove={onMoveSun} setIsDragging={setIsDragging} />
        ) : (
          <Moon position={moonPos} isSelected={selectedEntityId === 'moon'} onClick={() => onSelectEntity('moon')} onMove={onMoveMoon} setIsDragging={setIsDragging} />
        )}

        <Ground tiles={tiles} selectedTileId={selectedTileId} onSelectTile={onSelectTile} />
        
        <HeatmapSystem data={heatmap} maxVisits={maxVisits} />

        {/* Se o modo estiver ON, pinta a área no chão */}
        {isRouteTestingMode && <SpawnAreaVisualizer bounds={routeBounds} />}

        {entities.map((entity) => {
          if (entity.type === 'character') {
            return (
              <Character
                key={entity.id} id={entity.id} position={entity.position} name={entity.name}
                isSelected={selectedEntityId === entity.id}
                onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging}
              />
            );
          }
          if (entity.type === 'cactus') {
            return (
              <CactusObstacle
                key={entity.id} id={entity.id} position={entity.position}
                isSelected={selectedEntityId === entity.id}
                onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging}
              />
            );
          }
          if (entity.type === 'house') {
            return (
              <House
                key={entity.id} id={entity.id} position={entity.position}
                isSelected={selectedEntityId === entity.id}
                onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging}
              />
            );
          }
          return null;
        })}
      </Canvas>
    </div>
  );
}