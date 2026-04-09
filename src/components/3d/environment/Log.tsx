import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface LogProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function Log({ id, position, isSelected, onClick, onMove, setIsDragging }: LogProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  // Rotação levemente aleatória para não ficarem todos perfeitamente alinhados no chão
  const randomRotation = useMemo(() => Math.random() * Math.PI, []);

  useEffect(() => {
    if (meshRef.current) meshRef.current.position.set(...position);
  }, []);

  useFrame((state, delta) => {
    if (!dragging && meshRef.current) meshRef.current.position.lerp(targetPos, 8 * delta);
  });

  const handlePointerDown = (e: any) => {
    e.stopPropagation(); onClick(id); setDragging(true); setIsDragging(true);
    (e.target as any).setPointerCapture(e.pointerId);
  };

  const handlePointerUp = (e: any) => {
    e.stopPropagation(); setDragging(false); setIsDragging(false);
    (e.target as any).releasePointerCapture(e.pointerId);
    if (meshRef.current) onMove(id, [meshRef.current.position.x, position[1], meshRef.current.position.z]);
  };

  const handlePointerMove = (e: any) => {
    if (dragging && meshRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      if (e.ray.intersectPlane(dragPlane, intersectPoint)) {
        meshRef.current.position.set(intersectPoint.x, position[1], intersectPoint.z);
      }
    }
  };

  return (
    <mesh
      ref={meshRef}
      position={position}
      rotation={[Math.PI / 2, 0, randomRotation]} // Deitado no chão
      scale={dragging ? 1.2 : 1}
      castShadow
      receiveShadow
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
    >
      <cylinderGeometry args={[0.15, 0.15, 0.8, 8]} />
      <meshStandardMaterial color="#6b4423" emissive={isSelected ? "#ffffff" : "#000000"} emissiveIntensity={isSelected ? 0.2 : 0} />
      
      {/* Topo do tronco cortado (Círculos claros) */}
      <mesh position={[0, 0.41, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.14, 16]} />
        <meshStandardMaterial color="#cdaa7d" />
      </mesh>
      <mesh position={[0, -0.41, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.14, 16]} />
        <meshStandardMaterial color="#cdaa7d" />
      </mesh>
    </mesh>
  );
}