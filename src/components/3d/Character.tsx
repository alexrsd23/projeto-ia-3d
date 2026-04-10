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
  const groupRef = useRef<THREE.Mesh>(null);
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

  // === NOVO MOTOR DE ROTAÇÃO E MOVIMENTO (Minecraft Style) ===
// RENDER LOOP (60 FPS): Interpolação suave (Lerp) desacoplada da lógica!
useFrame((state, delta) => {
  // Garante que o personagem não está a ser arrastado e que o grupo existe
  if (!dragging && groupRef.current) {
    // 1. === CÁLCULO DE ROTAÇÃO FÍSICA (lookAt) ===
    // Calcula a distância real entre onde o personagem está agora e para onde ele quer ir.
    const dist = groupRef.current.position.distanceTo(targetPos);
    
    // Se a distância for significativa (> 0.05), ele rotaciona.
    // Isso evita rotações espasmódicas quando está quase a chegar ao alvo.
    if (dist > 0.05) {
      // Cria um vetor de alvo temporário.
      // Importante: Usamos groupRef.current.position.y para a coordenada 'y'.
      // Isso garante que ele gire apenas no eixo horizontal e não fique a olhar "para o chão".
      const lookAtTarget = new THREE.Vector3(targetPos.x, groupRef.current.position.y, targetPos.z);
      
      // A mágica do lookAt do Three.js: Gira todo o grupo para facear o alvo instantaneamente.
      groupRef.current.lookAt(lookAtTarget);
    }

    // 2. === MOVIMENTO SUAVE (Lerp) ===
    // Desliza a posição do personagem suavemente até o alvo.
    // O fator '8' define a velocidade do deslize. Quanto maior, mais rápido ele tenta alcançar o alvo.
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