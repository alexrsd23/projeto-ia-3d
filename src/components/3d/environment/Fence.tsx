import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Entity } from '../../../types';

interface FenceProps {
  id: string;
  position: [number, number, number];
  rotation?: number; // Agora é opcional, a cerca já não liga para isso
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  onRotate?: (id: string, rot: number) => void; 
  setIsDragging: (val: boolean) => void;
  allEntities: Entity[]; 
}

export default function Fence({ id, position, isSelected, onClick, onMove, setIsDragging, allEntities }: FenceProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  // === INTELIGÊNCIA 100% AUTÔNOMA ===
  const getNeighbor = (dx: number, dz: number) => allEntities?.find(e =>
    (e.type === 'fence' || e.type === 'gate' || e.type === 'damaged_fence') &&
    Math.abs(e.position[0] - (position[0] + dx)) < 0.1 && 
    Math.abs(e.position[2] - (position[2] + dz)) < 0.1
  );

  const north = getNeighbor(0, -2);
  const south = getNeighbor(0, 2);
  const east = getNeighbor(2, 0);
  const west = getNeighbor(-2, 0);

  const hasNeighbors = north || south || east || west;

  // Se NÃO tem vizinhos, desenha uma cerca Leste-Oeste padrão.
  // Se TEM vizinhos, desenha EXATAMENTE as conexões necessárias.
  const drawN = !!north;
  const drawS = !!south;
  const drawE = !!east || (!hasNeighbors);
  const drawW = !!west || (!hasNeighbors);

  useEffect(() => {
    if (groupRef.current) groupRef.current.position.set(...position);
  }, []);

  useFrame((state, delta) => {
    if (!dragging && groupRef.current) {
      groupRef.current.position.lerp(targetPos, 8 * delta);
    }
  });

  const handlePointerDown = (e: any) => {
    e.stopPropagation(); onClick(id); setDragging(true); setIsDragging(true);
    (e.target as any).setPointerCapture(e.pointerId);
  };

  const handlePointerUp = (e: any) => {
    e.stopPropagation(); setDragging(false); setIsDragging(false);
    (e.target as any).releasePointerCapture(e.pointerId);
    if (groupRef.current) onMove(id, [groupRef.current.position.x, position[1], groupRef.current.position.z]);
  };

  const handlePointerMove = (e: any) => {
    if (dragging && groupRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      if (e.ray.intersectPlane(dragPlane, intersectPoint)) {
        const clampedX = Math.round(intersectPoint.x / 2) * 2;
        const clampedZ = Math.round(intersectPoint.z / 2) * 2;
        groupRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  const fenceMaterial = useMemo(() => new THREE.MeshStandardMaterial({ 
    color: "#d4a373", roughness: 0.8, 
    emissive: isSelected ? "#ffffff" : "#000000", emissiveIntensity: isSelected ? 0.2 : 0 
  }), [isSelected]);

  return (
    <group ref={groupRef} position={position} scale={dragging ? 1.05 : 1} onPointerDown={handlePointerDown} onPointerUp={handlePointerUp} onPointerMove={handlePointerMove}>
      
      {/* POSTE CENTRAL (Sempre existe) */}
      <mesh position={[0, 0.5, 0]} castShadow receiveShadow material={fenceMaterial}>
        <boxGeometry args={[0.15, 1, 0.15]} />
      </mesh>

      {/* SEGMENTO LESTE (+X) */}
      {drawE && (
        <group>
          <mesh position={[0.5, 0.7, 0]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[1, 0.15, 0.05]} /></mesh>
          <mesh position={[0.5, 0.3, 0]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[1, 0.15, 0.05]} /></mesh>
          <mesh position={[0.8, 0.5, 0]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.15, 1, 0.15]} /></mesh>
        </group>
      )}

      {/* SEGMENTO OESTE (-X) */}
      {drawW && (
        <group>
          <mesh position={[-0.5, 0.7, 0]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[1, 0.15, 0.05]} /></mesh>
          <mesh position={[-0.5, 0.3, 0]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[1, 0.15, 0.05]} /></mesh>
          <mesh position={[-0.8, 0.5, 0]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.15, 1, 0.15]} /></mesh>
        </group>
      )}

      {/* SEGMENTO NORTE (-Z) */}
      {drawN && (
        <group>
          <mesh position={[0, 0.7, -0.5]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.05, 0.15, 1]} /></mesh>
          <mesh position={[0, 0.3, -0.5]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.05, 0.15, 1]} /></mesh>
          <mesh position={[0, 0.5, -0.8]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.15, 1, 0.15]} /></mesh>
        </group>
      )}

      {/* SEGMENTO SUL (+Z) */}
      {drawS && (
        <group>
          <mesh position={[0, 0.7, 0.5]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.05, 0.15, 1]} /></mesh>
          <mesh position={[0, 0.3, 0.5]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.05, 0.15, 1]} /></mesh>
          <mesh position={[0, 0.5, 0.8]} castShadow receiveShadow material={fenceMaterial}><boxGeometry args={[0.15, 1, 0.15]} /></mesh>
        </group>
      )}

    </group>
  );
}