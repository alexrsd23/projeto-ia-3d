import { Handle, Position } from 'reactflow';
import PolaroidAgentCard from './PolaroidAgentCard';

export default function FamilyNode({ data }: { data: any }) {
  return (
    <div style={{ position: 'relative' }}>
      {/* Ponto ALTO: Entrada de Genética Ancestral */}
      <Handle type="target" position={Position.Top} id="top" style={{ background: '#94a3b8', width: '12px', height: '12px', top: '-6px' }} />

      {/* Pontos LATERAIS ESQUERDOS (Para atrair o cônjuge à direita) */}
      <Handle type="source" position={Position.Left} id="left-source" style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Left} id="left-target" style={{ opacity: 0 }} />

      {/* Pontos LATERAIS DIREITOS (Para atrair o cônjuge à esquerda) */}
      <Handle type="source" position={Position.Right} id="right-source" style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Right} id="right-target" style={{ opacity: 0 }} />

      {/* Cartão do Agente */}
      <PolaroidAgentCard entity={data} />
      
      {/* Ponto BAIXO: Transmissão Genética para a Geração Seguinte */}
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: '#3b82f6', width: '12px', height: '12px', bottom: '-6px' }} />
    </div>
  );
}