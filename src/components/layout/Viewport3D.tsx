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
import SpawnAreaVisualizer from '../3d/environment/SpawnAreaVisualizer';
import RouteVisualizerSystem from '../3d/environment/RouteVisualizerSystem';
import Farmer from '../3d/Farmer';
import Woodcutter from '../3d/Woodcutter';
import Builder from '../3d/Builder';
import Tree from '../3d/environment/Tree';
import Stump from '../3d/environment/Stump';
import Log from '../3d/environment/Log';
import Stone from '../3d/environment/Stone';
import Fence from '../3d/environment/Fence';
import LootBag from '../3d/environment/LootBag'; import Wolf from '../3d/environment/Wolf';
import DamagedFence from '../3d/environment/DamagedFence';
import Gate from '../3d/environment/Gate';
import { Html } from '@react-three/drei';
import PlotVisualizer from '../3d/environment/ground/PlotVisualizer';
import type { Entity, TileData, PlotData } from '../../types';

interface RouteBounds {
  xMin: number; xMax: number; zMin: number; zMax: number;
}

interface Viewport3DProps {
  entities: any[];
  selectedEntityId: string | null;
  onSelectEntity: (id: string) => void;
  onDeselect: () => void;
  onMoveEntity: (id: string, pos: [number, number, number]) => void;
  onRotateEntity: (id: string, rotation: number) => void;
  sunPos: [number, number, number];
  moonPos: [number, number, number];
  onMoveSun: (pos: [number, number, number]) => void;
  onMoveMoon: (pos: [number, number, number]) => void;
  isDay: boolean;
  tiles: TileData[];
  plots: PlotData[]; // <--- NOVO
  selectedTileId: string | null;
  onSelectTile: (id: string) => void;
  heatmap: { gridX: number, gridZ: number, visits: number }[];
  isRouteTestingMode: boolean;
  routeBounds: RouteBounds;
  analytics: any;
  showNames: boolean;
  isTerrainEditingMode: boolean;
}

export default function Viewport3D({
  entities, plots, selectedEntityId, onSelectEntity, onDeselect, onMoveEntity, onRotateEntity,
  sunPos, moonPos, onMoveSun, onMoveMoon, isDay, tiles, selectedTileId, onSelectTile, heatmap,
  isRouteTestingMode, routeBounds, analytics, showNames, isTerrainEditingMode
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

        <Ground 
          tiles={tiles} 
          selectedTileId={selectedTileId} 
          onSelectTile={isTerrainEditingMode ? onSelectTile : () => {}} 
        />

        {/* === NOVO: O VISUALIZADOR DE TERRENOS RESERVADOS === */}
        <PlotVisualizer plots={plots} />

        {/* O Mapa de Calor Clássico */}
        <HeatmapSystem data={heatmap} maxVisits={maxVisits} />

        {/* A NOVA Camada da Mente Colmeia (Azul e Vermelho) */}
        <RouteVisualizerSystem
          consolidatedPaths={analytics?.consolidatedPaths || []}
          lethalZones={analytics?.lethalZones || []}
        />

        {/* RESTAURADO: O Quadradinho do Modo de Teste de Rotas */}
        {isRouteTestingMode && <SpawnAreaVisualizer bounds={routeBounds} />}

        {entities.map((entity) => {
          if (entity.type === 'character') {
            return (
              <Character
                key={entity.id} id={entity.id} position={entity.position} name={entity.name}
                isSelected={selectedEntityId === entity.id}
                onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging}
                showNames={showNames}
              />
            );
          }
          // === RENDERIZAÇÃO DOS AGENTES EVOLUTIVOS (Com DNA) ===
          if (entity.type === 'farmer' || entity.type === 'woodcutter' || entity.type === 'builder') {

            // Escolhe qual o boneco correto a montar
            const CharacterComponent =
              entity.type === 'farmer' ? Farmer :
                entity.type === 'woodcutter' ? Woodcutter : Builder;

            return (
              <CharacterComponent
                key={entity.id}
                id={entity.id}
                position={entity.position}
                name={entity.name}
                hunger={entity.hunger}
                health={entity.health}

                // === AQUI ESTÁ O DNA QUE ESTAVA FALTANDO! ===
                color={entity.color}
                sex={entity.sex}
                trustLevel={entity.trustLevel}
                lieLevel={entity.lieLevel}
                // ============================================

                isSelected={selectedEntityId === entity.id}
                onClick={onSelectEntity}
                onMove={onMoveEntity}
                setIsDragging={setIsDragging}
                showNames={showNames}
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
          if (entity.type === 'tree') {
            return <Tree key={entity.id} id={entity.id} position={entity.position} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging} />;
          }
          if (entity.type === 'stump') {
            return <Stump key={entity.id} id={entity.id} position={entity.position} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging} />;
          }
          if (entity.type === 'log') {
            return <Log key={entity.id} id={entity.id} position={entity.position} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging} />;
          }
          if (entity.type === 'stone') {
            return <Stone key={entity.id} id={entity.id} position={entity.position} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging} />;
          }
          if (entity.type === 'loot') {
            return <LootBag key={entity.id} id={entity.id} position={entity.position} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} />;
          }
          if (entity.type === 'wolf') {
            return <Wolf key={entity.id} id={entity.id} position={entity.position} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging} />;
          }
          if (entity.type === 'damaged_fence') {
            return <DamagedFence key={entity.id} id={entity.id} position={entity.position} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} setIsDragging={setIsDragging} />;
          }
          if (entity.type === 'fence') {
            return <Fence key={entity.id} id={entity.id} position={entity.position} rotation={entity.rotation || 0} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} onRotate={onRotateEntity} setIsDragging={setIsDragging} allEntities={entities} />;
          }
          if (entity.type === 'gate') {
            return <Gate key={entity.id} id={entity.id} position={entity.position} rotation={entity.rotation || 0} isSelected={selectedEntityId === entity.id} onClick={onSelectEntity} onMove={onMoveEntity} onRotate={onRotateEntity} setIsDragging={setIsDragging} allEntities={entities} />;
          }
          return null;
        })}
      </Canvas>
    </div>
  );
}