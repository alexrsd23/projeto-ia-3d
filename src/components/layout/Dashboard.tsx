import { useState, useEffect } from 'react';
import { type Entity } from '../../types';

interface RouteBounds {
  xMin: number; xMax: number; zMin: number; zMax: number;
}

interface DashboardProps {
  onAddEntity: (type: 'house' | 'character' | 'cactus') => void;
  isRunning: boolean;
  onToggleSimulation: () => void;
  selectedEntity: Entity | undefined;
  onSaveIdentity: (id: string, name: string, birthdate: string) => void;
  onToggleDayNight: () => void;
  isDay: boolean;
  selectedTile: any;
  onPlow: (id: string) => void;
  onPlant: (id: string) => void;
  onDeselectTile: () => void;
  
  // NOVAS PROPS DO MODO DE TESTE
  isRouteTestingMode: boolean;
  onToggleRouteTesting: () => void;
  routeBounds: RouteBounds;
  setRouteBounds: (bounds: RouteBounds) => void;
}

export default function Dashboard({
  onAddEntity, isRunning, onToggleSimulation, selectedEntity,
  onSaveIdentity, onToggleDayNight, isDay, selectedTile,
  onPlow, onPlant, onDeselectTile,
  isRouteTestingMode, onToggleRouteTesting, routeBounds, setRouteBounds
}: DashboardProps) {
  
  const [name, setName] = useState('');
  const [birthdate, setBirthdate] = useState('');
  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);

  useEffect(() => {
    if (selectedEntity) {
      setName(selectedEntity.name || '');
      setBirthdate(selectedEntity.birthdate || '');
    }
  }, [selectedEntity]);

  return (
    <div className="premium-dashboard">
      
      <div className="dashboard-top">
        <div className="dashboard-header">
          <h2>Painel de Controlo</h2>
          <p className="subtitle">Simulador IA 3D</p>
        </div>

        <div className="action-group">
          <button className={`btn-premium ${isRunning ? 'btn-danger' : 'btn-success'}`} onClick={onToggleSimulation}>
            {isRunning ? '⏸ Pausar Simulação' : '▶️ Iniciar Simulação'}
          </button>

          <button className={`btn-premium ${isDay ? 'btn-warning' : 'btn-dark'}`} onClick={onToggleDayNight}>
            {isDay ? '🌙 Mudar para Noite' : '☀️ Mudar para Dia'}
          </button>

          {/* NOVO: TOGGLE MODO DE TESTE */}
          <button className={`btn-premium ${isRouteTestingMode ? 'btn-action' : 'btn-dark'}`} onClick={onToggleRouteTesting}>
            {isRouteTestingMode ? '📍 Modo Teste de Rotas: ON' : '📍 Modo Teste de Rotas: OFF'}
          </button>
        </div>

        {/* NOVO: CONFIGURAÇÃO DE COORDENADAS (Só aparece se o modo estiver ativo) */}
        {isRouteTestingMode && (
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px', marginTop: '10px', border: '1px solid #3f4455' }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#cbd5e1' }}>Área de Spawn (Grid: 2x2)</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label className="premium-label" style={{marginTop: 0}}>X Mínimo</label>
                <input type="number" step="2" className="premium-input" value={routeBounds.xMin} onChange={e => setRouteBounds({...routeBounds, xMin: Number(e.target.value)})} />
              </div>
              <div>
                <label className="premium-label" style={{marginTop: 0}}>X Máximo</label>
                <input type="number" step="2" className="premium-input" value={routeBounds.xMax} onChange={e => setRouteBounds({...routeBounds, xMax: Number(e.target.value)})} />
              </div>
              <div>
                <label className="premium-label" style={{marginTop: 0}}>Z Mínimo</label>
                <input type="number" step="2" className="premium-input" value={routeBounds.zMin} onChange={e => setRouteBounds({...routeBounds, zMin: Number(e.target.value)})} />
              </div>
              <div>
                <label className="premium-label" style={{marginTop: 0}}>Z Máximo</label>
                <input type="number" step="2" className="premium-input" value={routeBounds.zMax} onChange={e => setRouteBounds({...routeBounds, zMax: Number(e.target.value)})} />
              </div>
            </div>
          </div>
        )}

        <div className="dropdown-section">
          <button className={`btn-premium btn-dropdown-toggle ${isAddMenuOpen ? 'active' : ''}`} onClick={() => setIsAddMenuOpen(!isAddMenuOpen)}>
            <span>➕ Adicionar Entidades</span>
            <span className="arrow">{isAddMenuOpen ? '▲' : '▼'}</span>
          </button>
          
          <div className={`dropdown-content ${isAddMenuOpen ? 'open' : ''}`}>
            <button className="btn-dropdown-item" onClick={() => onAddEntity('character')}>
              <span className="icon">👤⁺</span> Adicionar Pessoa
            </button>
            <button className="btn-dropdown-item" onClick={() => onAddEntity('house')}>
              <span className="icon">🏠⁺</span> Adicionar Casa
            </button>
            <button className="btn-dropdown-item" onClick={() => onAddEntity('cactus')}>
              <span className="icon">🌵⁺</span> Adicionar Cacto
            </button>
          </div>
        </div>
      </div>

      <div className="dashboard-bottom">
        {!selectedTile && (
          <div className="context-panel">
            <h3 className="panel-title">Informação da Entidade</h3>
            {selectedEntity ? (
              selectedEntity.type === 'character' ? (
                <div className="form-group">
                  <div className="status-badge">
                    <span className="id-tag">ID: {selectedEntity.id.split('-')[0]}</span>
                    <div className="stats-row">
                      <span>❤️ {selectedEntity.health ?? 'N/A'}</span>
                      <span>🍗 {selectedEntity.hunger ?? 'N/A'}</span>
                    </div>
                  </div>
                  <label className="premium-label">Nome:</label>
                  <input className="premium-input" value={name} onChange={(e) => setName(e.target.value)} />
                  <label className="premium-label">Data de Nascimento:</label>
                  <input className="premium-input" type="date" value={birthdate} onChange={(e) => setBirthdate(e.target.value)} />
                  <button className="btn-premium btn-action" style={{marginTop: '15px'}} onClick={() => onSaveIdentity(selectedEntity.id, name, birthdate)}>
                    💾 Guardar Alterações
                  </button>
                </div>
              ) : (
                <p className="empty-state">Estruturas (Casas/Cactos) não possuem atributos editáveis.</p>
              )
            ) : (
              <p className="empty-state">Selecione uma entidade no cenário 3D.</p>
            )}
          </div>
        )}

        {selectedTile && (
          <div className="context-panel farm-panel">
            <div className="panel-header-flex">
              <h3 className="panel-title">Terreno Selecionado</h3>
              <button className="btn-close-small" onClick={onDeselectTile}>✕</button>
            </div>
            <div className="status-badge">
              <p><strong>Tipo:</strong> {selectedTile.type === 'grass' ? '🌱 Grama Selvagem' : '🟤 Terra Arada'}</p>
              <p><strong>Coord:</strong> X:{selectedTile.gridX} | Z:{selectedTile.gridZ}</p>
            </div>
            {selectedTile.type === 'grass' ? (
              <div className="action-box">
                <p>Deseja arar esta terra?</p>
                <div className="flex-row">
                  <button className="btn-premium btn-success" onClick={() => onPlow(selectedTile.id)}>✅ Sim</button>
                  <button className="btn-premium btn-danger" onClick={onDeselectTile}>❌ Não</button>
                </div>
              </div>
            ) : (
              <div className="action-box">
                <p>Plantação ({selectedTile.crops.length}/2)</p>
                {selectedTile.crops.length < 2 ? (
                  <button className="btn-premium btn-farm" onClick={() => onPlant(selectedTile.id)}>🥔 Plantar Batata</button>
                ) : (
                  <p className="warning-text">⚠️ Capacidade máxima atingida.</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}