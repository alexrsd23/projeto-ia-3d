import { useRef, useState, useMemo, useEffect, type Dispatch, type SetStateAction } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface WarehouseProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: Dispatch<SetStateAction<boolean>>;
}

export default function Warehouse({ id, position, isSelected, onClick, onMove, setIsDragging }: WarehouseProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  useEffect(() => {
    if (groupRef.current) groupRef.current.position.set(...position);
  }, [position]);

  useFrame((state, delta) => {
    if (groupRef.current && !dragging) {
      targetPos.set(...position);
      groupRef.current.position.lerp(targetPos, 8 * delta);
    }
  });

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    onClick(id);
    setDragging(true);
    setIsDragging(true);
    (e.target as any).setPointerCapture(e.pointerId);
  };

  const handlePointerUp = (e: any) => {
    e.stopPropagation();
    setDragging(false);
    setIsDragging(false);
    (e.target as any).releasePointerCapture(e.pointerId);
    
    if (groupRef.current) {
      // === A MATEMÁTICA CORRETA DO GRID SNAP PARA 4x2 ===
      // Eixo X (4m): Força o snap para ÍMPARES (ex: 1, 3, -1)
      const snapX = Math.round((groupRef.current.position.x - 1) / 2) * 2 + 1;
      
      // Eixo Z (2m): Força o snap para PARES (ex: 0, 2, -2)
      const snapZ = Math.round(groupRef.current.position.z / 2) * 2;
      
      onMove(id, [snapX, position[1], snapZ]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && groupRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      if (e.ray.intersectPlane(dragPlane, intersectPoint)) {
        const clampedX = Math.max(-24, Math.min(24, intersectPoint.x));
        const clampedZ = Math.max(-24, Math.min(24, intersectPoint.z));
        groupRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  return (
    <group 
      ref={groupRef} 
      position={position} 
      scale={dragging ? 1.05 : 1}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
    >
      <group position={[0, 0, 0]}>
        
        {/* CORPO PRINCIPAL */}
        <mesh castShadow receiveShadow position={[0, 1, 0]}>
          <boxGeometry args={[4, 2, 2]} />
          <meshStandardMaterial 
            color="#9c0000" 
            emissive={isSelected ? "#3b82f6" : "#000000"} 
            emissiveIntensity={isSelected ? 0.3 : 0} 
          />
        </mesh>

        {/* TELHADO */}
        {/* CORREÇÃO: Posição Y ajustada de 2.5 para 2.0 para colar no topo da caixa */}
        <mesh castShadow receiveShadow position={[0, 2.0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[1.2, 1.2, 4, 3, 1, false, 0, Math.PI]} />
          <meshStandardMaterial color="#334155" />
        </mesh>

        {/* PORTAS DUPLAS (Frente) */}
        {/* Topo da porta termina em Y = 1.6 */}
        <mesh position={[0, 0.8, 1.01]}>
          <boxGeometry args={[1.2, 1.6, 0.05]} />
          <meshStandardMaterial color="#ffffff" />
        </mesh>
        
        {/* Traço em X nas portas */}
        <mesh position={[0, 0.8, 1.04]} rotation={[0, 0, 0.7]}>
          <boxGeometry args={[0.1, 1.5, 0.02]} />
          <meshStandardMaterial color="#94a3b8" />
        </mesh>
        <mesh position={[0, 0.8, 1.04]} rotation={[0, 0, -0.7]}>
          <boxGeometry args={[0.1, 1.5, 0.02]} />
          <meshStandardMaterial color="#94a3b8" />
        </mesh>

        {/* JANELA SUPERIOR (Sótão) */}
        {/* CORREÇÃO: Ajustada para caber entre o topo da porta (1.6) e a base do telhado (2.0) */}
        <mesh position={[0, 1.8, 1.01]}>
          <boxGeometry args={[0.4, 0.4, 0.05]} />
          <meshStandardMaterial color="#fbbf24" emissive="#fbbf24" emissiveIntensity={0.2} />
        </mesh>
        
      </group>
    </group>
  );
}