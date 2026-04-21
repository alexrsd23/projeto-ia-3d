import { useRef, useState, useMemo, useEffect, type Dispatch, type SetStateAction } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface LogCabinProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: Dispatch<SetStateAction<boolean>>;
}

export default function LogCabin({ id, position, isSelected, onClick, onMove, setIsDragging }: LogCabinProps) {
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
      // === A MATEMÁTICA CORRETA DO GRID SNAP PARA 4x2 ===
      // Eixo X (4m): Força o snap para ÍMPARES (ex: 1, 3, -1)
      const snapX = Math.round((groupRef.current.position.x - 1) / 2) * 2 + 1;
      
      // Eixo Z (2m): Força o snap para PARES (ex: 0, 2, -2)
      const snapZ = Math.round(groupRef.current.position.z / 2) * 2;
      
      onMove(id, [snapX, position[1], snapZ]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && groupRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      if (e.ray.intersectPlane(dragPlane, intersectPoint)) {
        const clampedX = Math.max(-24, Math.min(24, intersectPoint.x));
        const clampedZ = Math.max(-24, Math.min(24, intersectPoint.z));
        groupRef.current.position.set(clampedX, position[1], clampedZ);
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
        
        {/* CORPO PRINCIPAL (Altura 1.6, centrada em 0.8) */}
        <mesh castShadow receiveShadow position={[0, 0.8, 0]}>
          <boxGeometry args={[4, 1.6, 2]} />
          <meshStandardMaterial 
            color="#78350f" 
            emissive={isSelected ? "#3b82f6" : "#000000"} 
            emissiveIntensity={isSelected ? 0.3 : 0} 
            roughness={0.9}
          />
        </mesh>

        {/* DETALHES DAS PAREDES */}
        {[0.2, 0.6, 1.0, 1.4].map((h, i) => (
          <group key={`log-lines-${i}`}>
            <mesh position={[0, h, 1.01]}><boxGeometry args={[4, 0.05, 0.02]} /><meshStandardMaterial color="#451a03" /></mesh>
            <mesh position={[0, h, -1.01]}><boxGeometry args={[4, 0.05, 0.02]} /><meshStandardMaterial color="#451a03" /></mesh>
          </group>
        ))}

        {/* TELHADO - CORRIGIDO */}
        {/* Descido para Y=1.6 e adicionado rotação de 45 graus (Math.PI/4) no Y para alinhar as faces */}
        <mesh 
          castShadow 
          receiveShadow 
          position={[0, 1.6 + 0.6, 0]} 
          rotation={[0, Math.PI / 4, 0]}
        >
          <coneGeometry args={[2.8, 1.2, 4]} />
          <meshStandardMaterial color="#3f6212" />
        </mesh>

        {/* PORTA PRINCIPAL */}
        <mesh position={[0, 0.6, 1.02]}>
          <boxGeometry args={[0.8, 1.2, 0.05]} />
          <meshStandardMaterial color="#451a03" />
        </mesh>
        
        {/* Maçaneta */}
        <mesh position={[0.3, 0.6, 1.05]}>
          <sphereGeometry args={[0.05]} />
          <meshStandardMaterial color="#fbbf24" metalness={0.8} />
        </mesh>

        {/* JANELA */}
        <mesh position={[-1.2, 0.8, 1.02]}>
          <boxGeometry args={[0.6, 0.6, 0.05]} />
          <meshStandardMaterial color="#93c5fd" opacity={0.6} transparent />
        </mesh>
        <mesh position={[-1.2, 0.8, 1.03]}><boxGeometry args={[0.05, 0.6, 0.06]} /><meshStandardMaterial color="#451a03" /></mesh>
        <mesh position={[-1.2, 0.8, 1.03]}><boxGeometry args={[0.6, 0.05, 0.06]} /><meshStandardMaterial color="#451a03" /></mesh>

        {/* CHAMINÉ - Ajustada posição para brotar do telhado corretamente */}
        <mesh castShadow position={[1.2, 1.8, -0.4]}>
          <boxGeometry args={[0.4, 1.2, 0.4]} />
          <meshStandardMaterial color="#64748b" />
        </mesh>
        
        {/* Fumo decorativo */}
        <mesh position={[1.2, 2.5, -0.4]}>
          <sphereGeometry args={[0.15, 8, 8]} />
          <meshBasicMaterial color="#cbd5e1" transparent opacity={0.4} />
        </mesh>

      </group>
    </group>
  );
}