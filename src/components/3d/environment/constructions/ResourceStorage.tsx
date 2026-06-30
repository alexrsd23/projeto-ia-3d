import { useRef, useState, useMemo, useEffect, type Dispatch, type SetStateAction } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ResourceStorageProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: Dispatch<SetStateAction<boolean>>;
}

export default function ResourceStorage({ id, position, isSelected, onClick, onMove, setIsDragging }: ResourceStorageProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  useEffect(() => {
    if (groupRef.current) groupRef.current.position.set(...position);
  }, [position]);

  useFrame((state, delta) => {
    if (groupRef.current && !dragging) {
      targetPos.set(...position);
      groupRef.current.position.lerp(targetPos, 8 * delta);
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
    
    if (groupRef.current) {
      const snapX = Math.round(groupRef.current.position.x / 2) * 2;
      const snapZ = Math.round(groupRef.current.position.z / 2) * 2;
      onMove(id, [snapX, position[1], snapZ]);
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
      scale={dragging ? 1.05 : 1}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
    >
      <group position={[0, 0, 0]}>
        
        {/* BASE DE PEDRA (4x2) */}
        <mesh receiveShadow position={[0, 0.1, 0]}>
          <boxGeometry args={[4, 0.2, 2]} />
          <meshStandardMaterial 
            color="#475569" 
            emissive={isSelected ? "#3b82f6" : "#000000"} 
            emissiveIntensity={isSelected ? 0.3 : 0}
          />
        </mesh>

        {/* PAREDES (Altura 1.6) */}
        {/* Traseira */}
        <mesh castShadow position={[0, 0.8, -0.95]}>
          <boxGeometry args={[4, 1.6, 0.1]} />
          <meshStandardMaterial color="#92400e" />
        </mesh>
        {/* Laterais */}
        <mesh castShadow position={[-1.95, 0.8, 0]}>
          <boxGeometry args={[0.1, 1.6, 2]} />
          <meshStandardMaterial color="#92400e" />
        </mesh>
        <mesh castShadow position={[1.95, 0.8, 0]}>
          <boxGeometry args={[0.1, 1.6, 2]} />
          <meshStandardMaterial color="#92400e" />
        </mesh>

        {/* TELHADO PRISMA (Wrapper para corrigir rotação) */}
        {/* O wrapper deita o cilindro 90 graus em Z ao longo do eixo X (largura da casa).
            Ajuste de posição Y para `2.1775` para maior precisão na base encostar no topo da parede (Y=1.6).
            O raio é 1.155 e a distância da base ao centro é 0.5775. 1.6 + 0.5775 = 2.1775.
        */}
        <group 
          position={[0, 2.1775, 0]} 
          rotation={[0, 0, Math.PI / 2]} // Deita o cilindro/prisma ao longo do eixo X
        >
          {/* O telhado real dentro do wrapper. Isola a rotação interna da geometria do Three.js.
              args: [RaioTop, RaioBottom, Altura(Largura da casa), Segmentos]
              Um triângulo equilátero com raio 1.155 tem base de ~2 unidades (profundidade da casa).
          */}
          <mesh 
            castShadow 
            rotation={[0, -Math.PI / 6, 0]} // Gira o triângulo interno -45 graus em seu eixo local Y para alinhar o topo com +Y global.
          >
            <cylinderGeometry args={[1.155, 1.155, 4, 3]} />
            <meshStandardMaterial color="#451a03" />
          </mesh>
        </group>

        {/* PILARES FRONTAIS */}
        <mesh castShadow position={[-1.8, 0.8, 0.9]}>
          <boxGeometry args={[0.15, 1.6, 0.15]} />
          <meshStandardMaterial color="#312e81" />
        </mesh>
        <mesh castShadow position={[1.8, 0.8, 0.9]}>
          <boxGeometry args={[0.15, 1.6, 0.15]} />
          <meshStandardMaterial color="#312e81" />
        </mesh>

        {/* RECURSOS INTERNOS */}
        <group position={[0, 0.3, 0]}>
          <mesh castShadow position={[-1, 0, 0]} rotation={[0, Math.PI / 2, 0]}>
            <cylinderGeometry args={[0.15, 0.15, 1.2, 8]} />
            <meshStandardMaterial color="#78350f" />
          </mesh>
          <mesh castShadow position={[1, 0, 0]}>
            <dodecahedronGeometry args={[0.4, 0]} />
            <meshStandardMaterial color="#64748b" />
          </mesh>
        </group>

      </group>
    </group>
  );
}