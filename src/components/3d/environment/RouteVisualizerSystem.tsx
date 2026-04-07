import * as THREE from 'three';

interface Coord { x: number; z: number }

interface RouteVisualizerProps {
  consolidatedPaths: Coord[];
  lethalZones: Coord[];
}

export default function RouteVisualizerSystem({ consolidatedPaths, lethalZones }: RouteVisualizerProps) {
  return (
    // Colocamos numa camada fina Y=-0.46, logo acima da Terra (-0.5) e do Heatmap (-0.48)
    <group position={[0, -0.46, 0]}>
      
      {/* 1. AS ROTAS ÓTIMAS (Azul Escuro Translúcido) */}
      {consolidatedPaths?.map((pos, idx) => (
        <mesh key={`path-${idx}`} position={[pos.x, 0, pos.z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[2, 2]} />
          <meshBasicMaterial color="#1e3a8a" transparent opacity={0.6} depthWrite={false} />
        </mesh>
      ))}

      {/* 2. AS ZONAS LETAIS CONHECIDAS PELA MENTE COLMEIA (Vermelho Brilhante) */}
      {lethalZones?.map((pos, idx) => (
        <mesh key={`danger-${idx}`} position={[pos.x, 0.01, pos.z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[2, 2]} />
          <meshBasicMaterial color="#ef4444" transparent opacity={0.8} depthWrite={false} />
        </mesh>
      ))}
      
    </group>
  );
}