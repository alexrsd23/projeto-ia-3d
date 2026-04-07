export interface Entity {
  id: string;
  type: 'house' | 'character' | 'cactus';
  position: [number, number, number];
  name?: string;
  birthdate?: string;
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

export interface SimulationEvent {
  id: string;
  level: 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  timestamp: string;
}

export interface RouteAnalytics {
  bestRoutes: { origin: string; steps: number; agent: string; actions: string[] }[];
  leaderboard: { name: string; successes: number; bestTime: number }[];
  stats: { origin: string; attempts: number; successes: number }[];
  consolidatedPaths: { x: number; z: number }[]; // NOVO
  lethalZones: { x: number; z: number }[];       // NOVO
}