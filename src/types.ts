export interface Entity {
  id: string;
  type: 'house' | 'character' | 'cactus' | 'farmer' | 'woodcutter' | 'builder' | 
  'tree' | 'stump' | 'log' | 'stone' | 'fence' | 'loot' | 'wolf' | 'damaged_fence' | 
  'gate' | 'warehouse' | 'resource_storage' | 'log_cabin' | 'blacksmith';
  position: [number, number, number];
  rotation?: number;
  name?: string;
  birthdate?: string;
  health?: number; 
  hunger?: number;
  inventoryJSON?: string;
  memoryJSON?: string;
  state?: string;
  color?: string;       // Hexadecimal da cor (ex: "#4169E1")
  sex?: 'M' | 'F';      // Sexo biológico
  profession?: string;  // Título da profissão
  trustLevel?: number;  // Nível de confiança (0-100)
  lieLevel?: number;    // Nível de mentira (0-100)
  married?: boolean;    // Estado civil
  age?: number;         // Idade biológica do agente
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
  level: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS'; // <-- ADICIONE O SUCCESS AQUI
  message: string;
  timestamp?: string;
}

export interface RouteAnalytics {
  bestRoutes: { origin: string; steps: number; agent: string; actions: string[] }[];
  leaderboard: { name: string; successes: number; bestTime: number }[];
  stats: { origin: string; attempts: number; successes: number }[];
  consolidatedPaths: { x: number; z: number }[]; // NOVO
  lethalZones: { x: number; z: number }[];       // NOVO
}

// Adicione ao types.ts
export interface PlotData {
  id: string;
  ownerId: string;
  startX: number;
  startZ: number;
  width: number;
  height: number;
  status: 'planned' | 'building' | 'ready';
}