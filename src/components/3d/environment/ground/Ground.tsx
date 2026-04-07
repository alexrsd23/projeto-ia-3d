import Tile from './Tile';
import type { TileData } from '../../../../types';

interface GroundProps {
  tiles: TileData[];
  selectedTileId: string | null;
  onSelectTile: (id: string) => void;
}

export default function Ground({ tiles, selectedTileId, onSelectTile }: GroundProps) {
  return (
    <group>
      <gridHelper 
        args={[50, 25, "#000000", "#000000"]} 
        position={[0, -0.49, 0]} 
        material-opacity={0.15}
        material-transparent={true}
      />

      {tiles.map(tile => (
        <Tile 
          key={tile.id} 
          data={tile} 
          isSelected={selectedTileId === tile.id}
          onClick={onSelectTile}
        />
      ))}
    </group>
  );
}