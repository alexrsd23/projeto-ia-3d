import { Edges } from '@react-three/drei';
import * as THREE from 'three';

interface SkyboxProps {
  isDay: boolean;
}

export default function Skybox({ isDay }: SkyboxProps) {
  const skyColor = isDay ? "#87CEEB" : "#0B1D3A";

  return (
    // Mudamos a posição de 24.5 para 24.4. 
    // Isso afunda a caixa um pouquinho, parando de piscar com o chão!
    <mesh position={[0, 24.4, 0]}>
      
      <boxGeometry args={[50, 50, 50]} />
      <meshBasicMaterial color={skyColor} side={THREE.BackSide} />
      
      <Edges 
        linewidth={2} 
        color="#000000" 
        transparent 
        opacity={0.15} 
      />
      
    </mesh>
  );
}