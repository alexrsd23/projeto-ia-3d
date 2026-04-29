import FarmerBust from './FarmerBust';
import BuilderBust from './BuilderBust';
import WoodcutterBust from './WoodcutterBust';
import BlacksmithBust from './BlacksmithBust';
import type { Entity } from '../../../types';

interface PolaroidAgentCardProps {
  entity: Entity;
}

export default function PolaroidAgentCard({ entity }: PolaroidAgentCardProps) {
  // Lógica de vida biológica e filtragem de loot
  const isDead = (entity.health !== undefined && entity.health <= 0) || entity.type === 'loot';
  const agentColor = entity.color || '#94a3b8';

  // === CORREÇÃO: Polimorfismo Visual com Fallback Seguro ===
  let BustComponent = FarmerBust; // Padrão
  if (entity.type === 'builder') BustComponent = BuilderBust;
  if (entity.type === 'woodcutter') BustComponent = WoodcutterBust;
  if (entity.type === 'blacksmith') BustComponent = BlacksmithBust;

  // === EXTRAÇÃO FINANCEIRA E DE INVENTÁRIO ===
  let plobs = 0;
  try {
    const inventory = entity.inventoryJSON ? JSON.parse(entity.inventoryJSON) : {};
    if (inventory.plobs !== undefined) {
      plobs = Number(inventory.plobs);
    }
  } catch (e) {
    console.error("Erro ao fazer parse do inventário na Polaroid:", e);
  }

  // === SANITIZAÇÃO DA PROFISSÃO ===
  // Garante que o texto se mantém coerente mesmo se o DB não preencher o campo 'profession'
  let displayProfession = entity.profession;
  if (!displayProfession) {
    if (entity.type === 'builder') displayProfession = 'Construtor';
    else if (entity.type === 'woodcutter') displayProfession = 'Lenhador';
    else if (entity.type === 'blacksmith') displayProfession = 'Ferreiro';
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
      
      {/* A "Foto" da Polaroid (Busto do Agente) */}
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

      {/* Os Dados (Nome, Profissão, Status e Finanças) */}
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

        {/* === CORREÇÃO: Formatação Numérica Segura === */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#64748b', marginTop: '10px', justifyContent: 'center' }}>
          <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: '12px', height: '12px' }}>
            <circle cx="50" cy="50" r="45" fill="#fef08a" stroke="#334155" strokeWidth="6" />
            <text x="50" y="65" textAnchor="middle" fill="#334155" fontSize="50" fontWeight="bold">P</text>
          </svg>
          <span style={{ fontWeight: 'bold', color: '#0f172a' }}>
            {plobs.toFixed(2)}
          </span>
          <span style={{ fontSize: '10px' }}>Plobs</span>
        </div>
      </div>
      
    </div>
  );
}