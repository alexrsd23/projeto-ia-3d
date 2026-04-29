import AdvancedCharacter, { type AdvancedCharacterProps } from './AdvancedCharacter';

export default function Blacksmith(props: Omit<AdvancedCharacterProps, 'children' | 'profession'>) {
  return (
    <AdvancedCharacter {...props} profession="Ferreiro">
      
      {/* Acessório 1: Avental de Couro (Overlay no peito do agente) */}
      <mesh position={[0, 0.4, 0.26]} castShadow>
        <planeGeometry args={[0.6, 0.7]} />
        <meshStandardMaterial color="#2d3748" roughness={0.9} />
      </mesh>
      
      {/* Acessório 2: Martelo Pesado de Forja (Na mão/cintura) */}
      <group position={[0.6, 0, 0]} rotation={[0, 0, -Math.PI / 8]}>
        {/* Cabo do Martelo */}
        <mesh position={[0, 0, 0]} castShadow>
          <cylinderGeometry args={[0.04, 0.04, 0.6, 8]} />
          <meshStandardMaterial color="#8b5a2b" />
        </mesh>
        {/* Cabeça de Metal do Martelo */}
        <mesh position={[0, 0.3, 0]} castShadow>
          <boxGeometry args={[0.25, 0.15, 0.15]} />
          <meshStandardMaterial color="#1e293b" metalness={0.7} roughness={0.3} />
        </mesh>
      </group>

    </AdvancedCharacter>
  );
}