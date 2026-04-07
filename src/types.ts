export interface Entity {
  id: string;
  type: 'house' | 'character';
  position: [number, number, number];
  name?: string;       // Novo
  birthdate?: string;  // Novo
}