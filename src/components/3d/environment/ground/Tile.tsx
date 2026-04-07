import { Edges } from '@react-three/drei';
import PotatoCrop from '../../crops/PotatoCrop';
import type { TileData } from '../../../../types';

interface TileProps {
  data: TileData;
  isSelected: boolean;
  onClick: (id: string) => void;
}

export default function Tile({ data, isSelected, onClick }: TileProps) {
  const isFarm = data.type === 'farm';
  
  // A cor muda se for terra arada e se estiver selecionada
  const baseColor = isFarm ? "#8B5A2B" : "#4f7942"; // Marrom terra ou Verde grama
  const highlightColor = isFarm ? "#a87c51" : "#6b9e59";

  return (
    <group position={[data.gridX, -0.5, data.gridZ]}>
      {/* O Quadrado de Chão (Plano 2D) */}
      <mesh 
        rotation={[-Math.PI / 2, 0, 0]} 
        receiveShadow
        onClick={(e) => {
          e.stopPropagation(); // Impede que o clique vaze para o céu/universo
          onClick(data.id);
        }}
      >
        <planeGeometry args={[2, 2]} />
        <meshStandardMaterial color={isSelected ? highlightColor : baseColor} />
        
        {/* Mostra uma borda branca suave quando clicado */}
        {isSelected && <Edges linewidth={2} color="#ffffff" />}
      </mesh>

      {/* Se for uma fazenda, renderiza as culturas que estão crescendo nela */}
      {isFarm && data.crops.map(crop => (
        <PotatoCrop 
          key={crop.id} 
          stage={crop.stage} 
          // O Y é 0.25 para a planta ficar levemente fincada na terra (-0.5 + 0.25 = -0.25)
          position={[crop.positionOffset[0], 0.25, crop.positionOffset[1]]} 
        />
      ))}
    </group>
  );
}