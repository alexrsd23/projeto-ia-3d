import { useRef, useState, useMemo } from 'react';
import * as THREE from 'three';

interface CactusProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
}

export default function CactusObstacle({ id, position, isSelected, onClick, onMove, setIsDragging }: CactusProps) {
  const groupRef = useRef<THREE.Group>(null);
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

    if (groupRef.current) {
      let finalX = groupRef.current.position.x;
      let finalZ = groupRef.current.position.z;

      // GRID SNAPPING: Arredonda para múltiplo de 2 (tamanho do Tile)
      finalX = Math.round(finalX / 2) * 2;
      finalZ = Math.round(finalZ / 2) * 2;

      // === AS DUAS LINHAS DE MATH.MAX/MIN FORAM APAGADAS DAQUI ===

      groupRef.current.position.set(finalX, position[1], finalZ);
      onMove(id, [finalX, position[1], finalZ]);
    }
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
    <group 
      ref={groupRef} 
      position={position}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
      scale={dragging ? 1.1 : 1}
    >
      <mesh position={[0, 1, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.3, 0.3, 2, 8]} />
        {/* Fica com tom mais amarelado/destacado quando selecionado */}
        <meshStandardMaterial color={isSelected ? "#3CB371" : "#2E8B57"} /> 
      </mesh>
      
      <mesh position={[-0.4, 1.2, 0]} rotation={[0, 0, Math.PI / 4]} castShadow>
        <cylinderGeometry args={[0.15, 0.15, 0.8, 8]} />
        <meshStandardMaterial color={isSelected ? "#3CB371" : "#2E8B57"} />
      </mesh>
      <mesh position={[0.4, 0.8, 0]} rotation={[0, 0, -Math.PI / 4]} castShadow>
        <cylinderGeometry args={[0.15, 0.15, 0.8, 8]} />
        <meshStandardMaterial color={isSelected ? "#3CB371" : "#2E8B57"} />
      </mesh>
    </group>
  );
}