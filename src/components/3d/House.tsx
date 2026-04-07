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
      // --- LÓGICA DE GRID SNAPPING (ENCAIXE) ---
      let finalX = meshRef.current.position.x;
      let finalZ = meshRef.current.position.z;

      // Arredonda para o múltiplo de 2 mais próximo (tamanho exato do nosso Tile)
      finalX = Math.round(finalX / 2) * 2;
      finalZ = Math.round(finalZ / 2) * 2;

      // Validação: Garante que o encaixe não jogue a casa para fora do mundo (-24 a 24)
      finalX = Math.max(-24, Math.min(24, finalX));
      finalZ = Math.max(-24, Math.min(24, finalZ));

      // 1. Atualiza visualmente na mesma hora para dar o efeito de "pulo" pro lugar certo
      meshRef.current.position.set(finalX, position[1], finalZ);

      // 2. Salva a nova coordenada perfeita no banco de dados
      onMove(id, [finalX, position[1], finalZ]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && meshRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      const hit = e.ray.intersectPlane(dragPlane, intersectPoint);
      if (hit) {
        // Movimentação livre durante o arrasto, mantendo o limite do mundo
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
      {/* Como o tamanho é [2, 2, 2] e a célula é [2, 2], a ocupação é integral! */}
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color={isSelected ? "#A0522D" : "#8B4513"} />
    </mesh>
  );
}