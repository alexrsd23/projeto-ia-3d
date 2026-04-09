import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface FenceProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function Fence({ id, position, isSelected, onClick, onMove, setIsDragging }: FenceProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

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
        // TRAVA NA GRADE: Encaixa perfeitamente de 2 em 2 metros
        const clampedX = Math.round(intersectPoint.x / 2) * 2;
        const clampedZ = Math.round(intersectPoint.z / 2) * 2;
        groupRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  const fenceMaterial = useMemo(() => new THREE.MeshStandardMaterial({ 
    color: "#d4a373", // Cor de madeira polida
    roughness: 0.8, 
    emissive: isSelected ? "#ffffff" : "#000000", 
    emissiveIntensity: isSelected ? 0.2 : 0 
  }), [isSelected]);

  return (
    <group ref={groupRef} position={position} scale={dragging ? 1.05 : 1}>
      
      <group onPointerDown={handlePointerDown} onPointerUp={handlePointerUp} onPointerMove={handlePointerMove}>
        {/* Postes Verticais (Estacas) */}
        <mesh position={[-0.8, 0.5, 0]} castShadow receiveShadow material={fenceMaterial}>
          <boxGeometry args={[0.15, 1, 0.15]} />
        </mesh>
        <mesh position={[0, 0.5, 0]} castShadow receiveShadow material={fenceMaterial}>
          <boxGeometry args={[0.15, 1, 0.15]} />
        </mesh>
        <mesh position={[0.8, 0.5, 0]} castShadow receiveShadow material={fenceMaterial}>
          <boxGeometry args={[0.15, 1, 0.15]} />
        </mesh>

        {/* Tábuas Horizontais ligando os postes */}
        <mesh position={[0, 0.7, 0]} castShadow receiveShadow material={fenceMaterial}>
          <boxGeometry args={[2, 0.15, 0.05]} />
        </mesh>
        <mesh position={[0, 0.3, 0]} castShadow receiveShadow material={fenceMaterial}>
          <boxGeometry args={[2, 0.15, 0.05]} />
        </mesh>
      </group>

    </group>
  );
}