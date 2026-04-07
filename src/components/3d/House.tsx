import { useRef, useState, useMemo } from 'react';
import * as THREE from 'three';

interface HouseProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function House({ id, position, isSelected, onClick, onMove, setIsDragging }: HouseProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);

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
      onMove(id, [meshRef.current.position.x, position[1], meshRef.current.position.z]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && meshRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      const hit = e.ray.intersectPlane(dragPlane, intersectPoint);
      if (hit) {
        // CLAMP: Impede que passe de 24 (desconta o volume da casa)
        const clampedX = Math.max(-24, Math.min(24, intersectPoint.x));
        const clampedZ = Math.max(-24, Math.min(24, intersectPoint.z));
        
        meshRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  return (
    <mesh
      ref={meshRef}
      position={position}
      castShadow
      receiveShadow
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
      scale={dragging ? 1.05 : 1}
    >
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color={isSelected ? "#A0522D" : "#8B4513"} />
    </mesh>
  );
}