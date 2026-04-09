import AdvancedCharacter, { type AdvancedCharacterProps } from './AdvancedCharacter';

export default function Farmer(props: Omit<AdvancedCharacterProps, 'children' | 'profession'>) {
  return (
    <AdvancedCharacter {...props} profession="Fazendeiro">
      
      {/* Acessório Exclusivo: Chapéu de Palha */}
      <mesh position={[0, 1.05, 0]} castShadow>
        <coneGeometry args={[0.8, 0.4, 16]} />
        <meshStandardMaterial color="#d4a373" />
      </mesh>
      
    </AdvancedCharacter>
  );
}