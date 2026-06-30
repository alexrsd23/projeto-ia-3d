import { useRef, useState, useMemo, useEffect, type Dispatch, type SetStateAction } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface DamagedFenceProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: Dispatch<SetStateAction<boolean>>;
}

export default function DamagedFence({ id, position, isSelected, onClick, onMove, setIsDragging }: DamagedFenceProps) {
  const meshRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  // === FÍSICA DE ARRASTAR BASEADA EM RAYCASTING ===
  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  useEffect(() => {
    if (meshRef.current) meshRef.current.position.set(...position);
  }, []);

  useFrame((state, delta) => {
    if (!dragging && meshRef.current) {
      targetPos.set(...position);
      meshRef.current.position.lerp(targetPos, 8 * delta);
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
    
    if (meshRef.current) {
      // Grid Snap 2x2 (Trava na Grelha)
      const snapX = Math.round(meshRef.current.position.x / 2) * 2;
      const snapZ = Math.round(meshRef.current.position.z / 2) * 2;
      onMove(id, [snapX, position[1], snapZ]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && meshRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      if (e.ray.intersectPlane(dragPlane, intersectPoint)) {
        // === BARREIRAS INVISÍVEIS REMOVIDAS ===
        // Agora a cerca pode ser arrastada livremente para as novas áreas de expansão
        meshRef.current.position.set(intersectPoint.x, position[1], intersectPoint.z);
      }
    }
  };

  return (
    <group 
      ref={meshRef} 
      position={position} 
      scale={dragging ? 1.05 : 1}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
    >
      {/* Pilar Esquerdo */}
      <mesh castShadow receiveShadow position={[-0.4, 0.3, 0]} rotation={[0, 0, 0.2]}>
        <boxGeometry args={[0.15, 0.6, 0.15]} />
        <meshStandardMaterial color="#5c4033" emissive={isSelected ? "#ffffff" : "#000000"} emissiveIntensity={isSelected ? 0.3 : 0} roughness={0.9} />
      </mesh>
      
      {/* Pilar Direito */}
      <mesh castShadow receiveShadow position={[0.4, 0.2, 0]}>
        <boxGeometry args={[0.15, 0.4, 0.15]} />
        <meshStandardMaterial color="#4a3b32" roughness={1.0} />
      </mesh>
      
      {/* Tábua Central Quebrada */}
      <mesh castShadow receiveShadow position={[0, 0.05, 0.2]} rotation={[Math.PI / 2, 0, 0.3]}>
        <boxGeometry args={[0.8, 0.1, 0.05]} />
        <meshStandardMaterial color="#3e2723" roughness={0.9} />
      </mesh>
      
      {/* Ícone de Alerta Flutuante (Avisa o Construtor) */}
      <mesh position={[0, 0.8, 0]}>
        <planeGeometry args={[0.3, 0.3]} />
        <meshBasicMaterial color="#ef4444" transparent opacity={0.8} />
      </mesh>
    </group>
  );
}