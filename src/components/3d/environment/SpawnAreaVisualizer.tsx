import { Edges } from '@react-three/drei';

interface RouteBounds {
  xMin: number;
  xMax: number;
  zMin: number;
  zMax: number;
}

interface SpawnAreaProps {
  bounds: RouteBounds;
}

export default function SpawnAreaVisualizer({ bounds }: SpawnAreaProps) {
  // Calcula a largura, profundidade e o centro matemático do retângulo
  const width = Math.abs(bounds.xMax - bounds.xMin);
  const depth = Math.abs(bounds.zMax - bounds.zMin);
  
  const centerX = bounds.xMin + width / 2;
  const centerZ = bounds.zMin + depth / 2;

  return (
    // Y = -0.47 para ficar ligeiramente acima do chão verde e do heatmap, evitando z-fighting
    <mesh position={[centerX, -0.47, centerZ]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[width, depth]} />
      <meshBasicMaterial color="#3b82f6" transparent opacity={0.25} depthWrite={false} />
      
      {/* Borda holográfica brilhante para demarcar a área */}
      <Edges color="#60a5fa" linewidth={2} />
    </mesh>
  );
}