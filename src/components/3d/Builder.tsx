import AdvancedCharacter, { type AdvancedCharacterProps } from './AdvancedCharacter';

export default function Builder(props: Omit<AdvancedCharacterProps, 'children' | 'profession'>) {
  return (
    <AdvancedCharacter {...props} profession="Construtor">
      
      {/* Acessório Exclusivo: Capacete Branco de Obra */}
      <mesh position={[0, 0.8, 0]} castShadow>
        {/* Usando SphereGeometry cortada ao meio para fazer um capacete */}
        <sphereGeometry args={[0.52, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2.2]} />
        <meshStandardMaterial color="#ffffff" roughness={0.2} metalness={0.1} />
      </mesh>
      
    </AdvancedCharacter>
  );
}