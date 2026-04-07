import { useRef, useState, useMemo, useEffect } from 'react';
import { Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface CharacterProps {
  id: string;
  position: [number, number, number];
  name?: string;
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
  showNames: boolean; // NOVO
}

export default function Character({ id, position, name, isSelected, onClick, onMove, setIsDragging, showNames }: CharacterProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  
  // Guardamos a posição desejada para onde o boneco deve deslizar
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  // Coloca o boneco na posição inicial exata ao nascer
  useEffect(() => {
    if (meshRef.current) {
      meshRef.current.position.set(...position);
    }
  }, []);

  // RENDER LOOP (60 FPS): Interpolação suave (Lerp) desacoplada da lógica!
  useFrame((state, delta) => {
    if (!dragging && meshRef.current) {
      // O fator '8' define a velocidade do deslize. Quanto maior, mais rápido ele tenta alcançar o alvo.
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
      onMove(id, [meshRef.current.position.x, position[1], meshRef.current.position.z]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && meshRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      const hit = e.ray.intersectPlane(dragPlane, intersectPoint);
      if (hit) {
        const clampedX = Math.max(-24.5, Math.min(24.5, intersectPoint.x));
        const clampedZ = Math.max(-24.5, Math.min(24.5, intersectPoint.z));
        meshRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  const isExplorer = name?.toLowerCase().includes('explorador');
  const defaultColor = isExplorer ? "#e74c3c" : "#4169E1"; 
  const highlightColor = isExplorer ? "#ff7675" : "#5A8BFF";

  return (
    <mesh
      ref={meshRef}
      castShadow
      receiveShadow
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
      scale={dragging ? 1.1 : 1}
    >
      <cylinderGeometry args={[0.5, 0.5, 2, 16]} />
      {/* Aqui usamos a nova cor! */}
      <meshStandardMaterial color={isSelected ? highlightColor : defaultColor} />
      {name && showNames && (
        <Html position={[0, 1.5, 0]} center>
          <div className="name-bubble">{name}</div>
        </Html>
      )}
    </mesh>
  );
}