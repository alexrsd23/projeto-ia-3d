import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface TreeProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function Tree({ id, position, isSelected, onClick, onMove, setIsDragging }: TreeProps) {
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
        // === BARREIRAS INVISÍVEIS REMOVIDAS ===
        groupRef.current.position.set(intersectPoint.x, position[1], intersectPoint.z);
      }
    }
  };

  return (
    <group ref={groupRef} position={position} scale={dragging ? 1.1 : 1}>
      {/* Tronco */}
      <mesh position={[0, 1, 0]} castShadow receiveShadow onPointerDown={handlePointerDown} onPointerUp={handlePointerUp} onPointerMove={handlePointerMove}>
        <cylinderGeometry args={[0.3, 0.4, 2, 8]} />
        <meshStandardMaterial color="#5c4033" emissive={isSelected ? "#ffffff" : "#000000"} emissiveIntensity={isSelected ? 0.2 : 0} roughness={0.9} />
      </mesh>
      
      {/* Folhagem (Copa da Árvore) */}
      <mesh position={[0, 2.5, 0]} castShadow receiveShadow>
        <dodecahedronGeometry args={[1.5, 1]} />
        <meshStandardMaterial color="#2e8b57" roughness={0.8} />
      </mesh>
    </group>
  );
}