import { useRef, useState, useMemo, useEffect } from 'react';
import { Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface FarmerProps {
  id: string;
  position: [number, number, number];
  name?: string;
  hunger?: number; // NOVO: Essencial para calcular a cor
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
  showNames: boolean;
}

export default function Farmer({ id, position, name, hunger = 100, isSelected, onClick, onMove, setIsDragging, showNames }: FarmerProps) {
  const groupRef = useRef<THREE.Group>(null);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  // Cores para a transição de Metabolismo Visual
  const healthyColor = useMemo(() => new THREE.Color("#4169E1"), []); // Azul 
  const starvingColor = useMemo(() => new THREE.Color("#e74c3c"), []); // Vermelho
  const currentColor = useMemo(() => new THREE.Color(), []);

  useEffect(() => {
    if (groupRef.current) {
      groupRef.current.position.set(...position);
    }
  }, []);

  // RENDER LOOP (60 FPS)
  useFrame((state, delta) => {
    if (!dragging && groupRef.current) {
      groupRef.current.position.lerp(targetPos, 8 * delta);
    }

    // LÓGICA DE COR: Interpola suavemente de Vermelho (0) para Azul (1)
    if (materialRef.current) {
      const hungerNormalized = Math.max(0, Math.min(100, hunger)) / 100;
      currentColor.lerpColors(starvingColor, healthyColor, hungerNormalized);
      materialRef.current.color.copy(currentColor);
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
      onMove(id, [groupRef.current.position.x, position[1], groupRef.current.position.z]);
    }
  };

  const handlePointerMove = (e: any) => {
    if (dragging && groupRef.current) {
      e.stopPropagation();
      const intersectPoint = new THREE.Vector3();
      const hit = e.ray.intersectPlane(dragPlane, intersectPoint);
      if (hit) {
        const clampedX = Math.max(-24.5, Math.min(24.5, intersectPoint.x));
        const clampedZ = Math.max(-24.5, Math.min(24.5, intersectPoint.z));
        groupRef.current.position.set(clampedX, position[1], clampedZ);
      }
    }
  };

  // LÓGICA DE SELEÇÃO POR HOVER (Basta passar o mouse para abrir as infos no Dashboard)
  const handlePointerOver = (e: any) => {
    e.stopPropagation();
    onClick(id); 
  };

  return (
    <group ref={groupRef} position={position} scale={dragging ? 1.1 : 1}>
      
      {/* Corpo do Fazendeiro (Cápsula em vez de cilindro para se destacar do Agente de rotas) */}
      <mesh
        castShadow
        receiveShadow
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerMove={handlePointerMove}
        onPointerOver={handlePointerOver}
      >
        <capsuleGeometry args={[0.5, 1, 16, 16]} />
        <meshStandardMaterial 
          ref={materialRef} 
          emissive={isSelected ? "#ffffff" : "#000000"} 
          emissiveIntensity={isSelected ? 0.2 : 0} 
        />
      </mesh>

      {/* Acessório Visual: O Chapéu de Palha */}
      <mesh position={[0, 1.05, 0]} castShadow>
        <coneGeometry args={[0.8, 0.4, 16]} />
        <meshStandardMaterial color="#d4a373" />
      </mesh>

      {/* Balão de Informação 3D */}
      {name && showNames && (
        <Html position={[0, 1.8, 0]} center>
          <div className="name-bubble" style={{ textAlign: 'center', padding: '6px 12px' }}>
            <div style={{ fontWeight: 'bold' }}>👨‍🌾 {name}</div>
            <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>
              Fome: {Math.round(hunger)}%
            </div>
          </div>
        </Html>
      )}
      
    </group>
  );
}