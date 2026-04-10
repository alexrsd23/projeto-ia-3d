import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface LootBagProps {
  id: string;
  position: [number, number, number];
  isSelected: boolean;
  onClick: (id: string) => void;
}

export default function LootBag({ id, position, isSelected, onClick }: LootBagProps) {
  const meshRef = useRef<THREE.Group>(null);
  const targetPos = useMemo(() => new THREE.Vector3(position[0], -0.4, position[2]), [position]); // Fica no chão

  useEffect(() => {
    if (meshRef.current) meshRef.current.position.set(position[0], -0.4, position[2]);
  }, []);

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.position.lerp(targetPos, 8 * delta);
      // O saco de dinheiro fica a pulsar/flutuar suavemente para chamar a atenção
      meshRef.current.position.y = -0.4 + Math.sin(state.clock.elapsedTime * 2) * 0.05;
    }
  });

  return (
    <group ref={meshRef} onClick={(e) => { e.stopPropagation(); onClick(id); }}>
      {/* Saco Base */}
      <mesh castShadow receiveShadow position={[0, 0.15, 0]}>
        <sphereGeometry args={[0.25, 16, 16]} />
        <meshStandardMaterial color="#8b5a2b" emissive={isSelected ? "#ffffff" : "#000000"} emissiveIntensity={isSelected ? 0.3 : 0} roughness={0.9} />
      </mesh>
      {/* Nó do Saco (Cordinha atada) */}
      <mesh castShadow position={[0, 0.4, 0]}>
        <coneGeometry args={[0.1, 0.15, 8]} />
        <meshStandardMaterial color="#5c4033" />
      </mesh>
      {/* Moedinha brilhante caída ao lado */}
      <mesh castShadow position={[0.2, 0.05, 0.1]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.08, 0.08, 0.02, 16]} />
        <meshStandardMaterial color="#fbbf24" metalness={0.8} roughness={0.2} />
      </mesh>
    </group>
  );
}