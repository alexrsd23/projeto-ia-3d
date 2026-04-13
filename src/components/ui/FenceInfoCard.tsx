import { type Entity } from '../../types';

interface FenceInfoCardProps {
  entity: Entity;
}

export default function FenceInfoCard({ entity }: FenceInfoCardProps) {
  const hp = entity.health ?? 100;
  const isDamaged = entity.type === 'damaged_fence' || hp <= 0;
  
  const statusColor = isDamaged ? '#ef4444' : hp < 50 ? '#f59e0b' : '#10b981';
  const statusText = isDamaged ? 'Destruída (Ruínas)' : hp < 50 ? 'Danificada (Precisando Reparo)' : 'Estrutura Intacta';

  return (
    <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      
      {/* CABEÇALHO */}
      <div style={{ background: '#fcf8f3', padding: '12px', borderRadius: '8px', border: '1px solid #d4a373', borderLeft: `4px solid #d4a373` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ color: '#78350f', fontWeight: 700, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            ID: {entity.id.split('-')[0]}
          </span>
          <span style={{ background: '#d4a373', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, color: '#fff', textTransform: 'uppercase' }}>
            {entity.type === 'gate' ? 'Portão' : 'Cerca de Madeira'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: statusColor, fontWeight: 700 }}>
          <span style={{ fontSize: '16px' }}>{isDamaged ? '🚧' : '🧱'}</span>
          {statusText}
        </div>
      </div>

      {/* INTEGRIDADE ESTRUTURAL */}
      <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#475569', fontWeight: 700, marginBottom: '4px' }}>
          <span>🛠️ Integridade Físico (HP)</span><span>{Math.round(hp)} / 100</span>
        </div>
        <div style={{ width: '100%', height: '10px', background: '#cbd5e1', borderRadius: '5px', overflow: 'hidden' }}>
          <div style={{ width: `${Math.max(0, Math.min(100, hp))}%`, height: '100%', background: statusColor, transition: 'width 0.3s' }} />
        </div>
      </div>
      
    </div>
  );
}