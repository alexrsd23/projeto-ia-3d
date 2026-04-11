import { Handle, Position } from 'reactflow';
import PolaroidAgentCard from './PolaroidAgentCard';

export default function FamilyNode({ data }: { data: any }) {
  return (
    <div style={{ position: 'relative' }}>
      {/* Ponto de conexão SUPERIOR (De onde vêm os pais) */}
      <Handle 
        type="target" 
        position={Position.Top} 
        style={{ background: '#94a3b8', width: '12px', height: '12px', top: '-6px' }} 
      />
      
      {/* O SEU CARTÃO POLAROID INTACTO! Passamos os dados para ele. */}
      <PolaroidAgentCard entity={data} />
      
      {/* Ponto de conexão INFERIOR (Para onde vão os filhos) */}
      <Handle 
        type="source" 
        position={Position.Bottom} 
        style={{ background: '#3b82f6', width: '12px', height: '12px', bottom: '-6px' }} 
      />
    </div>
  );
}