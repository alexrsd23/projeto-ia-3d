import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface StoneProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function Stone({ id, position, isSelected, onClick, onMove, setIsDragging }: StoneProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);
  
  // Rotação aleatória para que as pedras não pareçam todas clonadas na mesma posição
  const randomRotation = useMemo(() => Math.random() * Math.PI, []);

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
        const clampedX = Math.max(-24.5, Math.min(24.5, intersectPoint.x));
        const clampedZ = Math.max(-24.5, Math.min(24.5, intersectPoint.z));
        groupRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  return (
    <group ref={groupRef} position={position} rotation={[0, randomRotation, 0]} scale={dragging ? 1.1 : 1}>
      {/* Usando um Dodecaedro para dar aquele visual de "Rocha Low Poly" perfeita */}
      <mesh position={[0, 0.4, 0]} castShadow receiveShadow onPointerDown={handlePointerDown} onPointerUp={handlePointerUp} onPointerMove={handlePointerMove}>
        <dodecahedronGeometry args={[0.5, 0]} />
        <meshStandardMaterial 
          color="#7f8c8d" 
          roughness={0.9} 
          emissive={isSelected ? "#ffffff" : "#000000"} 
          emissiveIntensity={isSelected ? 0.2 : 0} 
        />
      </mesh>
      
      {/* Pequena pedrinha de detalhe na base */}
      <mesh position={[0.3, 0.15, 0.2]} castShadow receiveShadow>
        <dodecahedronGeometry args={[0.2, 0]} />
        <meshStandardMaterial color="#95a5a6" roughness={1} />
      </mesh>
    </group>
  );
}