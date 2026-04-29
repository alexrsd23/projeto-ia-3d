import { useState, useEffect } from 'react';
import { type Entity } from '../../types';
import InventoryCard from './InventoryCard';

interface CharacterInfoCardProps {
  entity: Entity;
  onSaveIdentity: (id: string, name: string, birthdate: string) => void;
}

export default function CharacterInfoCard({ entity, onSaveIdentity }: CharacterInfoCardProps) {
  const [name, setName] = useState(entity.name || '');
  const [birthdate, setBirthdate] = useState(entity.birthdate || '');
  const isMarried = entity.married === true;

  // Sincroniza os inputs se a entidade selecionada mudar no 3D
  useEffect(() => {
    setName(entity.name || '');
    setBirthdate(entity.birthdate || '');
  }, [entity]);

  // 1. Processamento do Livro de Memórias
  let memory = { foodCount: 0, farmCount: 0, hazardCount: 0 };
  try {
    const memoryJSON = (entity as any).memoryJSON;
    if (memoryJSON) {
      const parsedMem = JSON.parse(memoryJSON);
      memory.foodCount = Object.keys(parsedMem.food || {}).length;
      memory.farmCount = Object.keys(parsedMem.farms || {}).length;
      memory.hazardCount = Object.keys(parsedMem.hazards || {}).length;
    }
  } catch (e) {
    console.error("Erro ao ler memória:", e);
  }

  // 2. Sistema de Humor / Estado Psicológico
  let moodIcon = "🚶";
  let moodText = "Explorando pacificamente";
  let moodColor = "#3b82f6";

  const currentState = (entity as any).state || "UNKNOWN";
  const hungerLevel = entity.hunger ?? 100;

  // Adapta o texto baseando-se na profissão
  if (currentState === "FARMER" || currentState === "CRAFTING" || currentState === "CHOPPING" || currentState === "BUILDING") {
    if (entity.type === 'woodcutter') { moodIcon = "🪓"; moodText = "Cortando madeira"; moodColor = "#8b5a2b"; }
    else if (entity.type === 'builder') { moodIcon = "🧱"; moodText = "Construindo estruturas"; moodColor = "#64748b"; }
    else if (entity.type === 'blacksmith') { moodIcon = "⚒️"; moodText = "Forjando no calor da bigorna"; moodColor = "#334155"; } // <--- HUMOR DO FERREIRO
    else { moodIcon = "👨‍🌾"; moodText = "Trabalhando na agricultura"; moodColor = "#10b981"; }
  } else if (currentState === "SEEK_FOOD" || (hungerLevel < 70 && hungerLevel >= 30)) {
    moodIcon = "🔍"; moodText = "Procurando comida"; moodColor = "#d97706";
  } else if (currentState === "BROKEN_TOOL") {
    moodIcon = "🔧"; moodText = "Ferramenta quebrada! Buscando reparo"; moodColor = "#64748b";
  } else if (currentState === "EMERGENCY_EAT" || hungerLevel < 30) {
    moodIcon = "🚨"; moodText = "Desesperado por sobrevivência"; moodColor = "#ef4444";
  }

  const toolHp = (entity as any).toolHp ?? 100;

  return (
    <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* CABEÇALHO DO PERSONAGEM, DNA & HUMOR */}
      <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: `1px solid ${moodColor}40`, borderLeft: `4px solid ${moodColor}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ color: '#334155', fontWeight: 700, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            ID: {entity.id.split('-')[0]}
            {/* O DNA da Cor e do Sexo renderizado aqui! */}
            {entity.color && (
              <span title="DNA Cromossômico" style={{ width: '12px', height: '12px', borderRadius: '50%', background: entity.color, border: '1px solid #cbd5e1', display: 'inline-block' }}></span>
            )}
            {entity.sex && <span style={{ color: entity.sex === 'M' ? '#3b82f6' : '#ec4899' }}>{entity.sex === 'M' ? '♂' : '♀'}</span>}
          </span>
          <span style={{ background: '#e2e8f0', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
            {entity.profession || entity.type}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: moodColor, fontWeight: 600 }}>
          <span style={{ fontSize: '16px' }}>{moodIcon}</span>
          {moodText}
        </div>
      </div>

      {/* SINAIS VITAIS & FERRAMENTAS */}
      <div style={{ display: 'flex', gap: '8px' }}>
        
        {/* VIDA */}
        <div style={{ flex: 1, background: '#fff5f5', padding: '8px', borderRadius: '8px', border: '1px solid #fecaca' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#b91c1c', fontWeight: 700, marginBottom: '4px' }}>
            <span>❤️ Vida</span><span>{Math.round(entity.health ?? 0)}%</span>
          </div>
          <div style={{ width: '100%', height: '6px', background: '#f87171', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${entity.health ?? 0}%`, height: '100%', background: '#dc2626', transition: 'width 0.3s' }} />
          </div>
        </div>

        {/* FOME */}
        <div style={{ flex: 1, background: '#f0fdf4', padding: '8px', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#15803d', fontWeight: 700, marginBottom: '4px' }}>
            <span>🍗 Fome</span><span>{Math.round(entity.hunger ?? 0)}%</span>
          </div>
          <div style={{ width: '100%', height: '6px', background: '#86efac', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${entity.hunger ?? 0}%`, height: '100%', background: '#16a34a', transition: 'width 0.3s' }} />
          </div>
        </div>

        {/* NOVO: DURABILIDADE DA FERRAMENTA (Apenas para Trabalhadores) */}
        {['farmer', 'woodcutter', 'builder', 'blacksmith'].includes(entity.type) && (
          <div style={{ flex: 1, background: '#f1f5f9', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#475569', fontWeight: 700, marginBottom: '4px' }}>
              <span>⚒️ Item</span><span>{Math.round(toolHp)}%</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#cbd5e1', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${toolHp}%`, height: '100%', background: '#475569', transition: 'width 0.3s' }} />
            </div>
          </div>
        )}
      </div>

      {/* === INVENTÁRIO DINÂMICO === */}
      <InventoryCard entityType={entity.type} inventoryJSON={entity.inventoryJSON} />

      {/* === PAINEL DE MEMÓRIA (CORREÇÃO: Reintroduzido na UI) === */}
      <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <h4 style={{ fontSize: '12px', color: '#475569', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          🧠 Livro de Memórias
        </h4>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ color: '#d97706', fontSize: '16px', marginBottom: '2px' }}>🥔</span>
            <span style={{ color: '#64748b', fontWeight: 600 }}>Comida: <span style={{ color: '#d97706' }}>{memory.foodCount}</span></span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ color: '#10b981', fontSize: '16px', marginBottom: '2px' }}>🌾</span>
            <span style={{ color: '#64748b', fontWeight: 600 }}>Terras: <span style={{ color: '#10b981' }}>{memory.farmCount}</span></span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ color: '#ef4444', fontSize: '16px', marginBottom: '2px' }}>⚠️</span>
            <span style={{ color: '#64748b', fontWeight: 600 }}>Perigos: <span style={{ color: '#ef4444' }}>{memory.hazardCount}</span></span>
          </div>
        </div>
      </div>

      {/* PAINEL DE ATRIBUTOS SOCIAIS (O DNA Mental) */}
      <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <h4 style={{ fontSize: '12px', color: '#475569', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          🧬 Atributos Genéticos & Sociais
        </h4>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ color: '#10b981', fontSize: '16px', marginBottom: '2px' }}>🤝</span>
            <span style={{ color: '#64748b', fontWeight: 600 }}>Confiança: <span style={{ color: '#10b981' }}>{entity.trustLevel ?? 50}</span></span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ color: '#ef4444', fontSize: '16px', marginBottom: '2px' }}>🎭</span>
            <span style={{ color: '#64748b', fontWeight: 600 }}>Mentira: <span style={{ color: '#ef4444' }}>{entity.lieLevel ?? 0}</span></span>
          </div>

          {/* === CORREÇÃO APLICADA AQUI === */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ color: '#8b5cf6', fontSize: '16px', marginBottom: '2px' }}>{isMarried ? '💍' : '👤'}</span>
            <span style={{ color: '#64748b', fontWeight: 600 }}>Estado: <span style={{ color: '#8b5cf6' }}>{isMarried ? 'Casado(a)' : 'Solteiro'}</span></span>
          </div>
        </div>
      </div>

      {/* EDIÇÃO DE IDENTIDADE */}
      <div style={{ marginTop: '4px' }}>
        <label className="light-label">Nome:</label>
        <input className="light-input" style={{ marginBottom: '10px' }} value={name} onChange={(e) => setName(e.target.value)} />
        <label className="light-label">Data de Nascimento:</label>
        <input className="light-input" type="date" value={birthdate} onChange={(e) => setBirthdate(e.target.value)} />
        <button className="btn-light-action primary" style={{ marginTop: '10px' }} onClick={() => onSaveIdentity(entity.id, name, birthdate)}>
          💾 Guardar Alterações
        </button>
      </div>

    </div>
  );
}