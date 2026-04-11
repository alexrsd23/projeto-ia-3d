import FarmerBust from './FarmerBust';
import BuilderBust from './BuilderBust';
import WoodcutterBust from './WoodcutterBust';
import type { Entity } from '../../../types';

interface PolaroidAgentCardProps {
  entity: Entity;
}

export default function PolaroidAgentCard({ entity }: PolaroidAgentCardProps) {
  // Lógica de vida
  const isDead = (entity.health !== undefined && entity.health <= 0) || entity.type === 'loot';
  const agentColor = entity.color || '#94a3b8';

  // === CORREÇÃO: Usar o 'type' interno do sistema que é 100% à prova de falhas ===
  let BustComponent = FarmerBust; // Default
  if (entity.type === 'builder') BustComponent = BuilderBust;
  if (entity.type === 'woodcutter') BustComponent = WoodcutterBust;

  // === NOVA LÓGICA: Extrair quantidade de Plobs do inventário ===
  const inventory = entity.inventoryJSON ? JSON.parse(entity.inventoryJSON) : {};
  const plobs = inventory.plobs !== undefined ? inventory.plobs : 0;

  // Garante que o texto em baixo da foto também fica sempre correto, mesmo se o BD não enviar a "profession"
  let displayProfession = entity.profession;
  if (!displayProfession) {
    if (entity.type === 'builder') displayProfession = 'Construtor';
    else if (entity.type === 'woodcutter') displayProfession = 'Lenhador';
    else if (entity.type === 'farmer') displayProfession = 'Fazendeiro';
    else displayProfession = 'Explorador';
  }

  return (
    <div style={{
      backgroundColor: '#ffffff',
      padding: '12px 12px 24px 12px',
      borderRadius: '2px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08)',
      width: '160px',
      display: 'flex',
      flexDirection: 'column',
      filter: isDead ? 'grayscale(100%) opacity(0.7)' : 'none',
      transition: 'all 0.2s ease',
      transform: 'rotate(-1deg)'
    }}>
      
      {/* A "Foto" da Polaroid */}
      <div style={{
        backgroundColor: '#f1f5f9',
        border: '1px solid #e2e8f0',
        height: '130px',
        marginBottom: '15px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-end',
        overflow: 'hidden'
      }}>
        <div style={{ width: '100px', height: '100px' }}>
          <BustComponent color={agentColor} />
        </div>
      </div>

      {/* Os Dados Escritos a "Caneta" */}
      <div style={{ textAlign: 'center', fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ 
          fontWeight: 'bold', 
          fontSize: '15px', 
          color: '#0f172a',
          textDecoration: isDead ? 'line-through' : 'none',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {entity.name || 'Desconhecido'}
        </div>
        
        <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', marginTop: '4px', letterSpacing: '0.5px' }}>
          {displayProfession}
        </div>
        
        <div style={{ 
          fontSize: '11px', 
          fontWeight: 'bold', 
          marginTop: '10px',
          padding: '4px 0',
          borderRadius: '4px',
          backgroundColor: isDead ? '#fee2e2' : '#dcfce7',
          color: isDead ? '#dc2626' : '#059669'
        }}>
          {isDead ? '💀 FALECIDO' : '❤️ VIVO'}
        </div>

        {/* === NOVO DIV: Quantidade de Plobs com Ícone === */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#64748b', marginTop: '10px', justifyContent: 'center' }}>
          <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: '12px', height: '12px' }}>
            <circle cx="50" cy="50" r="45" fill="#fef08a" stroke="#334155" strokeWidth="6" />
            <text x="50" y="65" textAnchor="middle" fill="#334155" fontSize="50" fontWeight="bold">P</text>
          </svg>
          <span style={{ fontWeight: 'bold', color: '#0f172a' }}>{plobs}</span>
          <span style={{ fontSize: '10px' }}>Plobs</span>
        </div>
      </div>
      
    </div>
  );
}