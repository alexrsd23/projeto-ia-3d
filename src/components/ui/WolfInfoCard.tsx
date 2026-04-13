import { type Entity } from '../../types';

interface WolfInfoCardProps {
  entity: Entity;
}

export default function WolfInfoCard({ entity }: WolfInfoCardProps) {
  const hp = entity.health ?? 100;
  const hunger = entity.hunger ?? 100;
  const state = (entity as any).state || "UNKNOWN";

  let moodIcon = "🐺";
  let moodText = "Patrulhando pacificamente";
  let moodColor = "#64748b"; // Cinza (Neutro)

  if (state === "HUNTING" || state === "ATTACK_AGENT" || state === "ATTACK_FENCE") {
    moodIcon = "🩸";
    moodText = "A CAÇAR PRESAS!";
    moodColor = "#dc2626"; // Vermelho
  } else if (state === "FLEEING") {
    moodIcon = "💨";
    moodText = "Fugindo";
    moodColor = "#d97706"; // Laranja
  }

  return (
    <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      
      {/* CABEÇALHO */}
      <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: `1px solid ${moodColor}40`, borderLeft: `4px solid ${moodColor}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ color: '#334155', fontWeight: 700, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            ID: {entity.id.split('-')[0]}
          </span>
          <span style={{ background: '#1e293b', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, color: '#f8fafc', textTransform: 'uppercase' }}>
            Lobo Selvagem
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: moodColor, fontWeight: 700 }}>
          <span style={{ fontSize: '16px' }}>{moodIcon}</span>
          {moodText}
        </div>
      </div>

      {/* SINAIS VITAIS DO PREDADOR */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <div style={{ flex: 1, background: '#fff5f5', padding: '10px', borderRadius: '8px', border: '1px solid #fecaca' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#b91c1c', fontWeight: 700, marginBottom: '4px' }}>
            <span>❤️ Vida</span><span>{Math.round(hp)}%</span>
          </div>
          <div style={{ width: '100%', height: '6px', background: '#f87171', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${hp}%`, height: '100%', background: '#dc2626', transition: 'width 0.3s' }} />
          </div>
        </div>

        <div style={{ flex: 1, background: '#fefce8', padding: '10px', borderRadius: '8px', border: '1px solid #fef08a' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#a16207', fontWeight: 700, marginBottom: '4px' }}>
            <span>🍗 Fome</span><span>{Math.round(hunger)}%</span>
          </div>
          <div style={{ width: '100%', height: '6px', background: '#fde047', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${hunger}%`, height: '100%', background: '#ca8a04', transition: 'width 0.3s' }} />
          </div>
        </div>
      </div>
      
    </div>
  );
}