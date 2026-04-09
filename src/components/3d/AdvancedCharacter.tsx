import { useRef, useState, useMemo, useEffect } from 'react';
import { Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Exportamos a interface para que as classes filhas possam herdá-la
export interface AdvancedCharacterProps {
  id: string;
  position: [number, number, number];
  name?: string;
  hunger?: number;
  health?: number;
  // === NOVOS ATRIBUTOS GENÉTICOS E SOCIAIS ===
  color?: string;       // Cor base da roupa/corpo
  sex?: 'M' | 'F';      // Sexo do agente
  profession?: string;  // Profissão
  trustLevel?: number;  // Nível de Confiança (0 a 100)
  lieLevel?: number;    // Nível de Mentira/Egoísmo (0 a 100)
  // ===========================================
  isSelected: boolean;
  onClick: (id: string) => void;
  onMove: (id: string, pos: [number, number, number]) => void;
  setIsDragging: (val: boolean) => void;
  showNames: boolean;
  children?: React.ReactNode; // AQUI ENTRAM OS ACESSÓRIOS DAS CLASSES FILHAS!
}

export default function AdvancedCharacter({
  id, position, name, hunger = 100, health = 100,
  color = "#4169E1", sex = 'M', profession = "Desempregado",
  trustLevel = 50, lieLevel = 0,
  isSelected, onClick, onMove, setIsDragging, showNames, children
}: AdvancedCharacterProps) {
  const groupRef = useRef<THREE.Group>(null);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);
  const [dragging, setDragging] = useState(false);

  const dragPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(0, 1, 0), -position[1]), [position[1]]);
  const targetPos = useMemo(() => new THREE.Vector3(...position), [position]);

  // Transição de cor (Mistura a cor base do boneco com vermelho se estiver morrendo de fome/sem vida)
  const baseColor = useMemo(() => new THREE.Color(color), [color]);
  const dangerColor = useMemo(() => new THREE.Color("#e74c3c"), []); 
  const currentColor = useMemo(() => new THREE.Color(), []);

  useEffect(() => {
    if (groupRef.current) {
      groupRef.current.position.set(...position);
    }
  }, []);

  useFrame((state, delta) => {
    if (!dragging && groupRef.current) {
      groupRef.current.position.lerp(targetPos, 8 * delta);
    }

    if (materialRef.current) {
      const condition = Math.min(hunger, health); // Fica vermelho pelo status mais baixo
      const normalized = Math.max(0, Math.min(100, condition)) / 100;
      currentColor.lerpColors(dangerColor, baseColor, normalized);
      materialRef.current.color.copy(currentColor);
    }
  });

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    onClick(id);
    setDragging(true); setIsDragging(true); 
    (e.target as any).setPointerCapture(e.pointerId); 
  };

  const handlePointerUp = (e: any) => {
    e.stopPropagation();
    setDragging(false); setIsDragging(false); 
    (e.target as any).releasePointerCapture(e.pointerId);
    if (groupRef.current) onMove(id, [groupRef.current.position.x, position[1], groupRef.current.position.z]);
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

  return (
    <group ref={groupRef} position={position} scale={dragging ? 1.1 : 1}>
      
      {/* Corpo Base Genérico */}
      <mesh
        castShadow receiveShadow
        onPointerDown={handlePointerDown} onPointerUp={handlePointerUp}
        onPointerMove={handlePointerMove} onPointerOver={(e) => { e.stopPropagation(); onClick(id); }}
      >
        <capsuleGeometry args={[0.5, 1, 16, 16]} />
        <meshStandardMaterial ref={materialRef} emissive={isSelected ? "#ffffff" : "#000000"} emissiveIntensity={isSelected ? 0.2 : 0} />
      </mesh>

      {/* AQUI É ONDE O CHAPÉU, MACHADO OU CAPACETE SERÃO RENDERIZADOS */}
      {children}

      {/* Balão de Informação Expandido */}
      {name && showNames && (
        <Html position={[0, 2.2, 0]} center>
          <div className="name-bubble" style={{ textAlign: 'center', padding: '6px 12px', minWidth: '120px' }}>
            <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{name} {sex === 'M' ? '♂' : '♀'}</div>
            <div style={{ fontSize: '10px', color: '#3b82f6', fontWeight: 'bold', textTransform: 'uppercase' }}>{profession}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginTop: '4px', borderTop: '1px solid #eee', paddingTop: '4px' }}>
              <span title="Confiança" style={{ color: '#10b981' }}>🤝 {Math.round(trustLevel)}</span>
              <span title="Mentira" style={{ color: '#ef4444' }}>🎭 {Math.round(lieLevel)}</span>
            </div>
          </div>
        </Html>
      )}
    </group>
  );
}