import { useState, useEffect } from 'react';
import { type Entity } from '../../types';

interface DashboardProps {
  onAddEntity: (type: 'house' | 'character') => void;
  isRunning: boolean;
  onToggleSimulation: () => void;
  selectedEntity: Entity | undefined; // Novo
  onSaveIdentity: (id: string, name: string, birthdate: string) => void; // Novo
  onToggleDayNight: () => void;
  isDay: boolean;
  selectedTile: any;
  onPlow: (id: string) => void;
  onPlant: (id: string) => void;
  onDeselectTile: () => void;
}

export default function Dashboard({ onAddEntity, isRunning, onToggleSimulation, selectedEntity, onSaveIdentity, onToggleDayNight, isDay, selectedTile, onPlow, onPlant, onDeselectTile }: DashboardProps) {
  // Estados temporários para o formulário
  const [name, setName] = useState('');
  const [birthdate, setBirthdate] = useState('');

  // Quando clicar em um boneco diferente, atualiza o formulário
  useEffect(() => {
    if (selectedEntity) {
      setName(selectedEntity.name || '');
      setBirthdate(selectedEntity.birthdate || '');
    }
  }, [selectedEntity]);

  return (
    <div className="dashboard">
      <h2>Painel de Controle</h2>

      <button
        onClick={onToggleSimulation}
        style={{ backgroundColor: isRunning ? '#e74c3c' : '#2ecc71', fontWeight: 'bold' }}
      >
        {isRunning ? '⏸ Pausar Simulação' : '▶️ Iniciar Simulação'}
      </button>

      <button
        onClick={onToggleDayNight}
        style={{ backgroundColor: isDay ? '#f39c12' : '#34495e', fontWeight: 'bold' }}
      >
        {isDay ? '☀️ Mudar para Noite' : '🌙 Mudar para Dia'}
      </button>

      <button onClick={() => onAddEntity('house')}>Inserir Casa</button>
      <button onClick={() => onAddEntity('character')}>Inserir Pessoa</button>

      {/* PAINEL DE IDENTIDADE (Rodapé) */}
      <div className="identity-panel">
        {selectedEntity ? (
          selectedEntity.type === 'character' ? (
            <>
              <h3>Editar Identidade</h3>
              <small>ID: {selectedEntity.id.split('-')[0]}</small>

              {/* O NOVO MOSTRADOR DE STATUS */}
              <div style={{ backgroundColor: '#2c3e50', padding: '10px', borderRadius: '5px', margin: '10px 0' }}>
                <p style={{ margin: 0, fontSize: '14px' }}>❤️ Vida: {selectedEntity.health ?? 'N/A'}</p>
                <p style={{ margin: 0, fontSize: '14px' }}>🍗 Fome: {selectedEntity.hunger ?? 'N/A'}</p>
              </div>

              <label>Nome:</label>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex: Bob" />

              <label>Data de Nasc.:</label>
              <input type="date" value={birthdate} onChange={(e) => setBirthdate(e.target.value)} />

              <button
                style={{ backgroundColor: '#f39c12', marginTop: '10px' }}
                onClick={() => onSaveIdentity(selectedEntity.id, name, birthdate)}
              >
                Salvar Identidade
              </button>
            </>
          ) : (
            <p>Selecione uma Pessoa (Casas não têm nome).</p>
          )
        ) : (
          <p>Clique em um boneco no cenário para editar.</p>
        )}
      </div>

      {/* PAINEL DE AGRICULTURA */}
      {selectedTile && (
        <div className="identity-panel" style={{ backgroundColor: '#27ae60', marginTop: '10px' }}>
          <h3>Terreno Selecionado</h3>
          <p>Tipo: {selectedTile.type === 'grass' ? '🌱 Grama Selvagem' : '🟤 Terra Arada'}</p>
          <p>Posição: X:{selectedTile.gridX} Z:{selectedTile.gridZ}</p>

          {selectedTile.type === 'grass' ? (
            <div>
              <p style={{ margin: '10px 0', fontWeight: 'bold' }}>Arar esta terra?</p>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button style={{ backgroundColor: '#2ecc71', flex: 1 }} onClick={() => onPlow(selectedTile.id)}>✅ Sim</button>
                <button style={{ backgroundColor: '#e74c3c', flex: 1 }} onClick={onDeselectTile}>❌ Não</button>
              </div>
            </div>
          ) : (
            <div>
              <p style={{ margin: '10px 0', fontWeight: 'bold' }}>Plantação ({selectedTile.crops.length}/2)</p>
              {selectedTile.crops.length < 2 ? (
                <button 
                  style={{ backgroundColor: '#f1c40f', color: 'black', width: '100%' }} 
                  onClick={() => onPlant(selectedTile.id)}
                >
                  🥔 Plantar Batata
                </button>
              ) : (
                <p style={{ color: '#f1c40f', fontSize: '14px' }}>⚠️ Capacidade máxima atingida.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}