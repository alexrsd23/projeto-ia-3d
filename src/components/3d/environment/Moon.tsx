import { useRef, useState, useMemo } from 'react';
import * as THREE from 'three';

interface AstroProps {
  position: [number, number, number];
  isSelected: boolean;
  onClick: () => void;
  onMove: (pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function Moon({ position, isSelected, onClick, onMove, setIsDragging }: AstroProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    onClick();
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
      onMove([groupRef.current.position.x, position[1], groupRef.current.position.z]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && groupRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      const hit = e.ray.intersectPlane(dragPlane, intersectPoint);
      if (hit) {
        // CLAMP: Limite exato do céu (50x50 = -25 a +25)
        const clampedX = Math.max(-25, Math.min(25, intersectPoint.x));
        const clampedZ = Math.max(-25, Math.min(25, intersectPoint.z));
        
        groupRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  return (
    <group ref={groupRef} position={position}>
      <mesh
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerMove={handlePointerMove}
        scale={dragging ? 1.1 : 1}
      >
        <sphereGeometry args={[2, 32, 32]} />
        <meshBasicMaterial color={isSelected ? "#D3D3D3" : "#A9A9A9"} />
      </mesh>
      <directionalLight intensity={0.3} color="#b5d1ff" />
    </group>
  );
}