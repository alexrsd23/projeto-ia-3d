export interface Entity {
  id: string;
  type: 'house' | 'character';
  position: [number, number, number];
  name?: string;
  birthdate?: string;
  
  // Novos atributos de simulação
  health?: number; 
  hunger?: number;
}

export interface CropData {
  id: string;
  type: 'potato';
  stage: 0 | 1 | 2; // 0: Semente/Broto, 1: Crescendo, 2: Pronta para Colher
  positionOffset: [number, number]; // Coordenadas locais [x, z] relativas ao tile pai
}

export interface TileData {
  id: string;
  gridX: number; // Posição global X no mundo
  gridZ: number; // Posição global Z no mundo
  type: 'grass' | 'farm'; // Grama comum ou Terra Arada
  crops: CropData[];
}