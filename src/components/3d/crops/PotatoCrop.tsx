interface PotatoCropProps {
  stage: 0 | 1 | 2;
  position: [number, number, number];
}

export default function PotatoCrop({ stage, position }: PotatoCropProps) {
  // A matemática de subdivisão 2x2: As plantas ficam menores para caberem no grid interno
  return (
    <mesh position={position} castShadow receiveShadow>
      {/* Estágio 0: Pequeno broto na terra */}
      {stage === 0 && <boxGeometry args={[0.3, 0.2, 0.3]} />}
      
      {/* Estágio 1: Planta média verde */}
      {stage === 1 && <boxGeometry args={[0.5, 0.5, 0.5]} />}
      
      {/* Estágio 2: Arbusto grande amarelado pronto para colher */}
      {stage === 2 && <boxGeometry args={[0.7, 0.8, 0.7]} />}
      
      <meshStandardMaterial color={stage === 2 ? "#DAA520" : "#228B22"} />
    </mesh>
  );
}