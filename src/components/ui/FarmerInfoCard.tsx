import { useState, useEffect } from 'react';
import { type Entity } from '../../types';
import InventoryCard from './InventoryCard'; // <-- A NOSSA IMPORTAÇÃO MODULAR!

interface FarmerInfoCardProps {
  farmer: Entity;
  onSaveIdentity: (id: string, name: string, birthdate: string) => void;
}

export default function FarmerInfoCard({ farmer, onSaveIdentity }: FarmerInfoCardProps) {
  const [name, setName] = useState(farmer.name || '');
  const [birthdate, setBirthdate] = useState(farmer.birthdate || '');

  // Sincroniza os inputs se o fazendeiro mudar
  useEffect(() => {
    setName(farmer.name || '');
    setBirthdate(farmer.birthdate || '');
  }, [farmer]);

  // 1. Processamento do Livro de Memórias (preparado para quando o backend enviar)
  let memory = { foodCount: 0, farmCount: 0, hazardCount: 0 };
  try {
    const memoryJSON = (farmer as any).memoryJSON;
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
  let moodColor = "#3b82f6"; // Azul

  // Usa o estado real do Cérebro se o backend enviar, senão deduz pela fome
  const currentState = (farmer as any).state || "UNKNOWN";
  const hungerLevel = farmer.hunger ?? 100;

  if (currentState === "FARMER") {
    moodIcon = "👨‍🌾"; moodText = "Trabalhando na agricultura"; moodColor = "#10b981";
  } else if (currentState === "SEEK_FOOD" || (hungerLevel < 70 && hungerLevel >= 30)) {
    moodIcon = "🔍"; moodText = "Procurando comida"; moodColor = "#d97706";
  } else if (currentState === "EMERGENCY_EAT" || hungerLevel < 30) {
    moodIcon = "🚨"; moodText = "Desesperado por sobrevivência"; moodColor = "#ef4444";
  }

  return (
    <div style={{ marginTop: '15px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      
      {/* CABEÇALHO DO PERSONAGEM & HUMOR */}
      <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: `1px solid ${moodColor}40`, borderLeft: `4px solid ${moodColor}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ color: '#334155', fontWeight: 700, fontSize: '14px' }}>ID: {farmer.id.split('-')[0]}</span>
          <span style={{ background: '#e2e8f0', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, color: '#64748b' }}>
            FAZENDEIRO
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: moodColor, fontWeight: 600 }}>
          <span style={{ fontSize: '16px' }}>{moodIcon}</span>
          {moodText}
        </div>
      </div>

      {/* SINAIS VITAIS (Barras de Progresso) */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <div style={{ flex: 1, background: '#fff5f5', padding: '10px', borderRadius: '8px', border: '1px solid #fecaca' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#b91c1c', fontWeight: 700, marginBottom: '4px' }}>
            <span>❤️ Vida</span>
            <span>{Math.round(farmer.health ?? 0)}%</span>
          </div>
          <div style={{ width: '100%', height: '6px', background: '#f87171', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${farmer.health ?? 0}%`, height: '100%', background: '#dc2626', transition: 'width 0.3s' }} />
          </div>
        </div>

        <div style={{ flex: 1, background: '#f0fdf4', padding: '10px', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#15803d', fontWeight: 700, marginBottom: '4px' }}>
            <span>🍗 Fome</span>
            <span>{Math.round(farmer.hunger ?? 0)}%</span>
          </div>
          <div style={{ width: '100%', height: '6px', background: '#86efac', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${farmer.hunger ?? 0}%`, height: '100%', background: '#16a34a', transition: 'width 0.3s' }} />
          </div>
        </div>
      </div>

      {/* === O NOSSO COMPONENTE ISOLADO DA MOCHILA (INVENTÁRIO) === */}
      <InventoryCard inventoryJSON={farmer.inventoryJSON} />

      {/* LIVRO DE MEMÓRIAS (Hipocampo) */}
      <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <h4 style={{ fontSize: '12px', color: '#475569', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          🧠 Conhecimento do Mapa
        </h4>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#64748b' }}>
          <span title="Comida Lembrada">📍 Batatas: <strong>{memory.foodCount}</strong></span>
          <span title="Terras Conhecidas">📍 Terras: <strong>{memory.farmCount}</strong></span>
          <span title="Perigos Mapeados">📍 Perigos: <strong>{memory.hazardCount}</strong></span>
        </div>
      </div>

      {/* EDIÇÃO DE IDENTIDADE */}
      <div style={{ marginTop: '4px' }}>
        <label className="light-label">Nome:</label>
        <input className="light-input" style={{ marginBottom: '10px' }} value={name} onChange={(e) => setName(e.target.value)} />
        <label className="light-label">Data de Nascimento:</label>
        <input className="light-input" type="date" value={birthdate} onChange={(e) => setBirthdate(e.target.value)} />
        <button className="btn-light-action primary" style={{ marginTop: '10px' }} onClick={() => onSaveIdentity(farmer.id, name, birthdate)}>
          💾 Guardar Alterações
        </button>
      </div>

    </div>
  );
}