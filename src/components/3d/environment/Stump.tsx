import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface StumpProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function Stump({ id, position, isSelected, onClick, onMove, setIsDragging }: StumpProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

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
        groupRef.current.position.set(intersectPoint.x, position[1], intersectPoint.z);
      }
    }
  };

  return (
    <group ref={groupRef} position={position} scale={dragging ? 1.1 : 1}>
      {/* Toco Cortado */}
      <mesh position={[0, 0.25, 0]} castShadow receiveShadow onPointerDown={handlePointerDown} onPointerUp={handlePointerUp} onPointerMove={handlePointerMove}>
        <cylinderGeometry args={[0.3, 0.4, 0.5, 8]} />
        <meshStandardMaterial color="#4a3020" emissive={isSelected ? "#ffffff" : "#000000"} emissiveIntensity={isSelected ? 0.2 : 0} />
      </mesh>
      
      {/* Anéis da Árvore (Parte de cima do toco) */}
      <mesh position={[0, 0.51, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[0.29, 16]} />
        <meshStandardMaterial color="#cdaa7d" />
      </mesh>
    </group>
  );
}