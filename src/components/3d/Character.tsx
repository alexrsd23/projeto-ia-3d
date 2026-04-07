import { useRef, useState, useMemo } from 'react';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

interface CharacterProps {
  id: string;
  position: [number, number, number];
  name?: string;
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function Character({ id, position, name, isSelected, onClick, onMove, setIsDragging }: CharacterProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [dragging, setDragging] = useState(false);

  // Cria um "chão" invisível matemático na altura exata do boneco
  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    onClick(id);
    setDragging(true);
    setIsDragging(true); // Trava a câmera global
    (e.target as any).setPointerCapture(e.pointerId); // Prende o mouse ao objeto
  };

  const handlePointerUp = (e: any) => {
    e.stopPropagation();
    setDragging(false);
    setIsDragging(false); // Libera a câmera
    (e.target as any).releasePointerCapture(e.pointerId);

    // Salva a posição final no Neo4j
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
        // CLAMP: Impede que o X e o Z passem de 24.5 (desconta 0.5 do raio do boneco)
        const clampedX = Math.max(-24.5, Math.min(24.5, intersectPoint.x));
        const clampedZ = Math.max(-24.5, Math.min(24.5, intersectPoint.z));
        
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
      scale={dragging ? 1.1 : 1} // Efeito visual de "pegou o objeto"
    >
      <cylinderGeometry args={[0.5, 0.5, 2, 16]} />
      {/* Fica um pouco mais claro quando selecionado */}
      <meshStandardMaterial color={isSelected ? "#5A8BFF" : "#4169E1"} />
      {name && (
        <Html position={[0, 1.5, 0]} center>
          <div className="name-bubble">{name}</div>
        </Html>
      )}
    </mesh>
  );
}