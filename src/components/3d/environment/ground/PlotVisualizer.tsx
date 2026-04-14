import { Line } from '@react-three/drei';
import type { PlotData } from '../../../../types'; // Ajuste o caminho se necessário

interface PlotVisualizerProps {
  plots: PlotData[];
}

export default function PlotVisualizer({ plots }: PlotVisualizerProps) {
  if (!plots || plots.length === 0) return null;

  return (
    <group>
      {plots.map((plot) => {
        // O passo do nosso mundo é de 2 em 2 metros
        const GRID_STEP = 2; 
        const maxX = plot.startX + (plot.width - 1) * GRID_STEP;
        const maxZ = plot.startZ + (plot.height - 1) * GRID_STEP;

        // Calculamos as bordas EXTERNAS do terreno.
        // Como o centro do bloco (Tile) é exato, a borda visual é o centro - 1 e centro + 1.
        const left = plot.startX - 1;
        const right = maxX + 1;
        const top = plot.startZ - 1;
        const bottom = maxZ + 1;
        
        // Colocamos a linha ligeiramente acima do chão (-0.5) para evitar z-fighting (cintilação)
        const y = -0.45; 

        // Os 5 pontos necessários para desenhar e fechar o quadrado perfeitamente
        const points: [number, number, number][] = [
          [left, y, top],
          [right, y, top],
          [right, y, bottom],
          [left, y, bottom],
          [left, y, top]
        ];

        // Cores semânticas: Amarelo para "Planejado" e Laranja para "Em Construção"
        const color = plot.status === 'planned' ? '#facc15' : '#f97316';

        return (
          <group key={plot.id}>
            {/* A Borda Tracejada Mágica */}
            <Line
              points={points}
              color={color}
              lineWidth={3}
              dashed={true}
              dashScale={2}
              dashSize={1}
              dashOffset={0}
            />
            
            {/* Opcional: Um fundo semi-transparente para demarcar a área comprada */}
            <mesh position={[(left + right) / 2, y - 0.01, (top + bottom) / 2]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[right - left, bottom - top]} />
              <meshBasicMaterial color={color} transparent opacity={0.08} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}