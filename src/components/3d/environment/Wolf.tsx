import { useRef, useState, useMemo, useEffect, type Dispatch, type SetStateAction } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface WolfProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: Dispatch<SetStateAction<boolean>>;
}

export default function Wolf({ id, position, isSelected, onClick, onMove, setIsDragging }: WolfProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [dragging, setDragging] = useState(false);

  // === FÍSICA DE ARRASTAR BASEADA EM RAYCASTING (Igual às Árvores/Cercas) ===
  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  useEffect(() => {
    if (groupRef.current) groupRef.current.position.set(...position);
  }, []);

  useFrame((state, delta) => {
    if (groupRef.current) {
      if (!dragging) {
        targetPos.set(...position);
        
        // === CORREÇÃO DA ROTAÇÃO (Instinto Predatório) ===
        const dx = targetPos.x - groupRef.current.position.x;
        const dz = targetPos.z - groupRef.current.position.z;
        const dist = Math.sqrt(dx * dx + dz * dz);

        if (dist > 0.05) {
          // Calcula o ângulo exato do movimento no eixo Y
          const targetAngle = Math.atan2(dx, dz);
          
          // Suaviza a matemática (Evita que o lobo dê um giro louco de 360º ao cruzar os eixos)
          let currentAngle = groupRef.current.rotation.y;
          while (currentAngle - targetAngle > Math.PI) currentAngle -= Math.PI * 2;
          while (targetAngle - currentAngle > Math.PI) currentAngle += Math.PI * 2;
          groupRef.current.rotation.y = currentAngle;

          // Interpolação suave (O lobo vira a cabeça de forma realista)
          groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, targetAngle, 10 * delta);
        }

        // Interpolação suave para o movimento
        groupRef.current.position.lerp(targetPos, 8 * delta);
        
        // Respiração/flutuação
        const hover = !isSelected ? Math.sin(state.clock.elapsedTime * 4) * 0.03 : 0;
        groupRef.current.position.y = position[1] + hover;
      }
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
      // Força o encaixe perfeito na grelha (Grid Snap 2x2) ao largar
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
        // Limita para que o lobo não seja arrastado para fora do mundo
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
      <group rotation={[0, 0, 0]}> 
        
        {/* CORPO */}
        <mesh castShadow receiveShadow position={[0, 0.35, 0]}>
          <boxGeometry args={[0.4, 0.4, 0.8]} />
          <meshStandardMaterial 
            color="#2d3748" 
            emissive={isSelected ? "#3b82f6" : "#000000"} 
            emissiveIntensity={isSelected ? 0.5 : 0} 
            roughness={0.8} 
          />
        </mesh>

        {/* CABEÇA */}
        <mesh castShadow position={[0, 0.5, 0.45]}>
          <boxGeometry args={[0.3, 0.3, 0.3]} />
          <meshStandardMaterial color="#1a202c" />
          
          {/* FOCINHO */}
          <mesh position={[0, -0.05, 0.2]}>
            <boxGeometry args={[0.15, 0.15, 0.2]} />
            <meshStandardMaterial color="#111827" />
          </mesh>

          {/* OLHOS */}
          <mesh position={[0.08, 0.05, 0.15]}><sphereGeometry args={[0.03]} /><meshBasicMaterial color="#ef4444" /></mesh>
          <mesh position={[-0.08, 0.05, 0.15]}><sphereGeometry args={[0.03]} /><meshBasicMaterial color="#ef4444" /></mesh>
        </mesh>

        {/* PERNAS */}
        <mesh castShadow position={[0.12, 0.15, 0.25]}><boxGeometry args={[0.1, 0.3, 0.1]} /><meshStandardMaterial color="#2d3748" /></mesh>
        <mesh castShadow position={[-0.12, 0.15, 0.25]}><boxGeometry args={[0.1, 0.3, 0.1]} /><meshStandardMaterial color="#2d3748" /></mesh>
        <mesh castShadow position={[0.12, 0.15, -0.25]}><boxGeometry args={[0.1, 0.3, 0.1]} /><meshStandardMaterial color="#2d3748" /></mesh>
        <mesh castShadow position={[-0.12, 0.15, -0.25]}><boxGeometry args={[0.1, 0.3, 0.1]} /><meshStandardMaterial color="#2d3748" /></mesh>

        {/* RABO */}
        <mesh castShadow position={[0, 0.45, -0.4]} rotation={[-Math.PI / 4, 0, 0]}>
          <boxGeometry args={[0.1, 0.1, 0.3]} />
          <meshStandardMaterial color="#1a202c" />
        </mesh>
      </group>
    </group>
  );
}