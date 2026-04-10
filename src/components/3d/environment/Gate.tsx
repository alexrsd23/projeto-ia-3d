import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Entity } from '../../../types';

interface GateProps {
  id: string;
  position: [number, number, number];
  rotation: number;
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  onRotate: (id: string, rot: number) => void; // Mantido na interface para não dar erro no TypeScript
  setIsDragging: (val: boolean) => void;
  allEntities: Entity[];
}

export default function Gate({ id, position, isSelected, onClick, onMove, setIsDragging, allEntities }: GateProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  // === INTELIGÊNCIA DE AUTO-ALINHAMENTO DO PORTÃO ===
  const getNeighbor = (dx: number, dz: number) => allEntities?.find(e =>
    (e.type === 'fence' || e.type === 'damaged_fence') &&
    Math.abs(e.position[0] - (position[0] + dx)) < 0.1 && 
    Math.abs(e.position[2] - (position[2] + dz)) < 0.1
  );

  const north = getNeighbor(0, -2);
  const south = getNeighbor(0, 2);
  const east = getNeighbor(2, 0);
  const west = getNeighbor(-2, 0);

  // O portão nasce Horizontal (0). Mas se ele detetar cercas apenas no eixo Norte/Sul, ele gira sozinho!
  let autoRotation = 0;
  if ((north || south) && !east && !west) {
    autoRotation = Math.PI / 2;
  }

  useEffect(() => {
    if (groupRef.current) groupRef.current.position.set(...position);
  }, []);

  useFrame((state, delta) => {
    if (!dragging && groupRef.current) groupRef.current.position.lerp(targetPos, 8 * delta);
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

  const gateMaterial = useMemo(() => new THREE.MeshStandardMaterial({ 
    color: "#b07d5b", 
    roughness: 0.9, 
    emissive: isSelected ? "#ffffff" : "#000000", emissiveIntensity: isSelected ? 0.2 : 0 
  }), [isSelected]);
  
  const hingeMaterial = new THREE.MeshStandardMaterial({ color: "#222222", metalness: 0.8 });

  return (
    <group ref={groupRef} position={position} scale={dragging ? 1.05 : 1}>
      
      {/* O BALÃO DE ROTAÇÃO FOI COMPLETAMENTE REMOVIDO DAQUI! */}

      <group rotation={[0, autoRotation, 0]} onPointerDown={handlePointerDown} onPointerUp={handlePointerUp} onPointerMove={handlePointerMove}>
        {/* Pilares Mestres do Portão */}
        <mesh position={[-0.85, 0.6, 0]} castShadow receiveShadow material={gateMaterial}><boxGeometry args={[0.2, 1.2, 0.2]} /></mesh>
        <mesh position={[0.85, 0.6, 0]} castShadow receiveShadow material={gateMaterial}><boxGeometry args={[0.2, 1.2, 0.2]} /></mesh>

        {/* Portas do Portão (Levemente abertas para dar efeito) */}
        <group position={[-0.75, 0, 0]} rotation={[0, -0.2, 0]}>
          <mesh position={[0.35, 0.45, 0]} castShadow receiveShadow material={gateMaterial}><boxGeometry args={[0.7, 0.8, 0.05]} /></mesh>
          <mesh position={[0, 0.7, 0.05]} castShadow material={hingeMaterial}><boxGeometry args={[0.1, 0.05, 0.05]} /></mesh>
          <mesh position={[0, 0.3, 0.05]} castShadow material={hingeMaterial}><boxGeometry args={[0.1, 0.05, 0.05]} /></mesh>
        </group>
        
        <group position={[0.75, 0, 0]} rotation={[0, 0.2, 0]}>
          <mesh position={[-0.35, 0.45, 0]} castShadow receiveShadow material={gateMaterial}><boxGeometry args={[0.7, 0.8, 0.05]} /></mesh>
          <mesh position={[0, 0.7, 0.05]} castShadow material={hingeMaterial}><boxGeometry args={[0.1, 0.05, 0.05]} /></mesh>
          <mesh position={[0, 0.3, 0.05]} castShadow material={hingeMaterial}><boxGeometry args={[0.1, 0.05, 0.05]} /></mesh>
        </group>
      </group>
    </group>
  );
}