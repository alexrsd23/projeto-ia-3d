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
}

export default function Dashboard({ onAddEntity, isRunning, onToggleSimulation, selectedEntity, onSaveIdentity, onToggleDayNight, isDay }: DashboardProps) {
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
    </div>
  );
}