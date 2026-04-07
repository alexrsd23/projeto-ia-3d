import * as THREE from 'three';

interface HeatmapTile {
  gridX: number;
  gridZ: number;
  visits: number;
}

interface HeatmapProps {
  data: HeatmapTile[];
  maxVisits: number; // Para normalizar as cores
}

export default function HeatmapSystem({ data, maxVisits }: HeatmapProps) {
  if (data.length === 0 || maxVisits === 0) return null;

  return (
    <group position={[0, -0.48, 0]}> {/* Ligeiramente acima da malha e do chão */}
      {data.map((tile, index) => {
        // Normaliza a intensidade entre 0 e 1
        const intensity = Math.min(tile.visits / maxVisits, 1);
        
        // Interpolação de cor: de Amarelo (baixa visita) para Vermelho (alta visita)
        const color = new THREE.Color().lerpColors(
          new THREE.Color("#ffff00"), 
          new THREE.Color("#ff0000"), 
          intensity
        );

        return (
          <mesh key={index} position={[tile.gridX, 0, tile.gridZ]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[2, 2]} />
            <meshBasicMaterial 
              color={color} 
              transparent 
              opacity={intensity * 0.6} // Fica mais opaco quanto mais visitado
              depthWrite={false}
            />
          </mesh>
        );
      })}
    </group>
  );
}