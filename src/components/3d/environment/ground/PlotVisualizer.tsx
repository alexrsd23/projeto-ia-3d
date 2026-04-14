import type { PlotData } from '../../../../types'; // Ajuste o caminho se necessário

interface PlotVisualizerProps {
  plots: PlotData[];
}

export default function PlotVisualizer({ plots }: PlotVisualizerProps) {
  if (!plots || plots.length === 0) return null;

  const GRID_STEP = 2;
  const y = -0.45; // Ligeiramente acima do chão para evitar cintilação (z-fighting)

  return (
    <group>
      {plots.map((plot) => {
        const tiles = [];
        
        // Cores baseadas no status
        const perimeterColor = plot.status === 'planned' ? '#3b82f6' : '#f97316'; // Azul (Cercas)
        const interiorColor = plot.status === 'planned' ? '#fbbf24' : '#ef4444';  // Amarelo/Avermelhado (Miolo)
        
        // Loop passando por cada bloco da grade da fazenda
        for (let i = 0; i < plot.width; i++) {
          for (let j = 0; j < plot.height; j++) {
            
            // Lógica: Se for a primeira/última linha ou coluna, é borda. Senão, é miolo.
            const isPerimeter = i === 0 || i === plot.width - 1 || j === 0 || j === plot.height - 1;
            const tileColor = isPerimeter ? perimeterColor : interiorColor;
            
            // Calcula a coordenada 3D exata do bloco
            const posX = plot.startX + i * GRID_STEP;
            const posZ = plot.startZ + j * GRID_STEP;

            tiles.push(
              <mesh key={`${plot.id}-${i}-${j}`} position={[posX, y, posZ]} rotation={[-Math.PI / 2, 0, 0]}>
                {/* 1.9 em vez de 2.0 deixa um pequeno vão entre os quadrados para formar uma grade visível igual ao seu print */}
                <planeGeometry args={[1.9, 1.9]} />
                <meshBasicMaterial color={tileColor} transparent opacity={0.5} />
              </mesh>
            );
          }
        }

        return (
          <group key={plot.id}>
            {tiles}
          </group>
        );
      })}
    </group>
  );
}