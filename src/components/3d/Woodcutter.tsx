import AdvancedCharacter, { type AdvancedCharacterProps } from './AdvancedCharacter';

export default function Woodcutter(props: Omit<AdvancedCharacterProps, 'children' | 'profession'>) {
  return (
    <AdvancedCharacter {...props} profession="Lenhador">
      
      {/* Acessório Exclusivo: Machado na mão/cintura */}
      <group position={[0.6, 0, 0]} rotation={[0, 0, -Math.PI / 8]}>
        {/* Cabo do Machado */}
        <mesh position={[0, 0, 0]} castShadow>
          <cylinderGeometry args={[0.05, 0.05, 0.8, 8]} />
          <meshStandardMaterial color="#8b5a2b" />
        </mesh>
        {/* Lâmina do Machado */}
        <mesh position={[0.15, 0.2, 0]} castShadow>
          <boxGeometry args={[0.3, 0.2, 0.05]} />
          <meshStandardMaterial color="#7f8c8d" metalness={0.3} roughness={0.4} />
        </mesh>
      </group>

    </AdvancedCharacter>
  );
}