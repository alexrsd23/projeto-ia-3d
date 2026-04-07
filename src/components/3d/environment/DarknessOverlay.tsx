import * as THREE from 'three';

interface DarknessOverlayProps {
  isDay: boolean;
}

export default function DarknessOverlay({ isDay }: DarknessOverlayProps) {
  const opacity = isDay ? 0 : 0.65;
  const ambientIntensity = isDay ? 0.8 : 0.1;

  return (
    <group>
      <ambientLight intensity={ambientIntensity} />
      
      {/* Afundamos para 24.4 acompanhando o Skybox */}
      <mesh position={[0, 24.4, 0]}>
        {/* Ajustamos para 49.9. Agora ela fica perfeitamente entre o Céu e o Chão */}
        <boxGeometry args={[49.9, 49.9, 49.9]} />
        <meshBasicMaterial 
          color="#5e7f93" 
          transparent 
          opacity={opacity} 
          side={THREE.DoubleSide} 
          depthWrite={false} 
        />
      </mesh>
    </group>
  );
}