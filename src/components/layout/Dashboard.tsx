import { useState, useEffect } from 'react';
import { type Entity } from '../../types';

interface RouteBounds {
  xMin: number; xMax: number; zMin: number; zMax: number;
}

interface DashboardProps {
  onAddEntity: (type: 'house' | 'character' | 'cactus', amount?: number) => void;
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
  isRouteTestingMode: boolean;
  onToggleRouteTesting: () => void;
  routeBounds: RouteBounds;
  setRouteBounds: (bounds: RouteBounds) => void;
  onKillAllAgents: () => void;
  onClearAIMemory: () => void;
  showNames: boolean;
  onToggleShowNames: () => void;
}

export default function Dashboard({
  onAddEntity, isRunning, onToggleSimulation, selectedEntity,
  onSaveIdentity, onToggleDayNight, isDay, selectedTile,
  onPlow, onPlant, onDeselectTile,
  isRouteTestingMode, onToggleRouteTesting, routeBounds, setRouteBounds,
  onKillAllAgents, showNames, onToggleShowNames, onClearAIMemory
}: DashboardProps) {
  
  const [name, setName] = useState('');
  const [birthdate, setBirthdate] = useState('');
  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);
  const [spawnAmount, setSpawnAmount] = useState<number>(1);

  useEffect(() => {
    if (selectedEntity) {
      setName(selectedEntity.name || '');
      setBirthdate(selectedEntity.birthdate || '');
    }
  }, [selectedEntity]);

  return (
    <div className="light-dashboard">
      
      <div className="dashboard-header">
        <h2>Painel de Controle</h2>
        <p className="subtitle">SIMULADOR IA 3D</p>
      </div>

      <div className="dashboard-content">
        
        {/* === GRID DE BOTÕES DE AÇÃO === */}
        <div className="action-grid">
          
          <button className="card-btn full" onClick={onToggleSimulation}>
            <span className="icon-large">{isRunning ? '⏸' : '▷'}</span>
            <span>{isRunning ? 'Pausar Simulação' : 'Iniciar Simulação'}</span>
          </button>

          <button className="card-btn half" onClick={onToggleDayNight}>
            <span className="icon-large">{isDay ? '🌙' : '☀️'}</span>
            <span>{isDay ? 'Mudar para Noite' : 'Mudar para Dia'}</span>
          </button>

          <button className={`card-btn half ${isRouteTestingMode ? 'active-blue' : ''}`} onClick={onToggleRouteTesting}>
            <span className="icon-large">📍</span>
            <span>Modo Teste de Rotas</span>
            <div className="toggle-container">
              <div className={`toggle-switch ${isRouteTestingMode ? 'on' : ''}`}>
                <div className="toggle-knob"></div>
              </div>
              <span className="toggle-label">{isRouteTestingMode ? 'ON' : 'OFF'}</span>
            </div>
          </button>

          <button className="card-btn full" onClick={onToggleShowNames}>
            <span className="icon-large">👁️</span>
            <span>Nomes Visíveis</span>
            <div className="toggle-container">
              <div className={`toggle-switch ${showNames ? 'on' : ''}`}>
                <div className="toggle-knob"></div>
              </div>
              <span className="toggle-label">{showNames ? 'ON' : 'OFF'}</span>
            </div>
          </button>

          <button className="card-btn half danger" onClick={onKillAllAgents}>
            <span className="icon-large">💀</span>
            <span>Expurgo: Matar Agentes</span>
          </button>

          <button className="card-btn half warning" onClick={onClearAIMemory}>
            <span className="icon-large">⌫</span>
            <span>Amnésia: Limpar Memória IA</span>
          </button>

        </div>

        {/* === ÁREA DE SPAWN (Só visível se modo de teste ON) === */}
        {isRouteTestingMode && (
          <div className="card-panel" style={{ marginTop: '0' }}>
            <div style={{ textAlign: 'center', marginBottom: '15px' }}>
              <span className="icon-large" style={{ color: '#64748b' }}>▦</span>
              <p className="panel-title-light" style={{ margin: '4px 0 2px' }}>Área de Spawn</p>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>(Grid: 2x2)</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label className="light-label">X Mínimo</label>
                <input type="number" step="2" className="light-input" value={routeBounds.xMin} onChange={e => setRouteBounds({...routeBounds, xMin: Number(e.target.value)})} />
              </div>
              <div>
                <label className="light-label">X Máximo</label>
                <input type="number" step="2" className="light-input" value={routeBounds.xMax} onChange={e => setRouteBounds({...routeBounds, xMax: Number(e.target.value)})} />
              </div>
              <div>
                <label className="light-label">Z Mínimo</label>
                <input type="number" step="2" className="light-input" value={routeBounds.zMin} onChange={e => setRouteBounds({...routeBounds, zMin: Number(e.target.value)})} />
              </div>
              <div>
                <label className="light-label">Z Máximo</label>
                <input type="number" step="2" className="light-input" value={routeBounds.zMax} onChange={e => setRouteBounds({...routeBounds, zMax: Number(e.target.value)})} />
              </div>
            </div>
          </div>
        )}

        {/* === MENU DE ADICIONAR ENTIDADES === */}
        <div className="card-panel" style={{ padding: '0', overflow: 'hidden' }}>
          <button className="btn-light-action" style={{ borderRadius: isAddMenuOpen ? '12px 12px 0 0' : '12px', padding: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} onClick={() => setIsAddMenuOpen(!isAddMenuOpen)}>
            <span>➕ Adicionar Entidades</span>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>{isAddMenuOpen ? '▲' : '▼'}</span>
          </button>
          
          <div className={`dropdown-content-light ${isAddMenuOpen ? 'open' : ''}`}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <label className="light-label" style={{ margin: 0 }}>Quantidade:</label>
              <input type="number" min="1" max="200" className="light-input" style={{ width: '60px', padding: '4px', margin: 0, textAlign: 'center' }} value={spawnAmount} onChange={(e) => setSpawnAmount(Math.max(1, Number(e.target.value)))} />
            </div>
            <button className="btn-dropdown-item-light" onClick={() => onAddEntity('character', spawnAmount)}>👤⁺ Adicionar Pessoa(s)</button>
            <button className="btn-dropdown-item-light" onClick={() => onAddEntity('house', spawnAmount)}>🏠⁺ Adicionar Casa(s)</button>
            <button className="btn-dropdown-item-light" onClick={() => onAddEntity('cactus', spawnAmount)}>🌵⁺ Adicionar Cacto(s)</button>
          </div>
        </div>

        {/* === INFORMAÇÃO DA ENTIDADE === */}
        {!selectedTile && (
          <div className="card-panel">
            <h3 className="panel-title-light">Informação da Entidade</h3>
            {selectedEntity ? (
              selectedEntity.type === 'character' ? (
                <div style={{ marginTop: '15px' }}>
                  <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', marginBottom: '15px', border: '1px solid #e2e8f0', fontSize: '13px' }}>
                    <span style={{ color: '#3b82f6', fontWeight: 600, fontFamily: 'monospace' }}>ID: {selectedEntity.id.split('-')[0]}</span>
                    <div style={{ display: 'flex', gap: '15px', marginTop: '8px', color: '#475569', fontWeight: 600 }}>
                      <span>❤️ {selectedEntity.health ?? 'N/A'}</span>
                      <span>🍗 {selectedEntity.hunger ?? 'N/A'}</span>
                    </div>
                  </div>
                  <label className="light-label">Nome:</label>
                  <input className="light-input" style={{ marginBottom: '10px' }} value={name} onChange={(e) => setName(e.target.value)} />
                  <label className="light-label">Data de Nascimento:</label>
                  <input className="light-input" type="date" value={birthdate} onChange={(e) => setBirthdate(e.target.value)} />
                  <button className="btn-light-action primary" style={{ marginTop: '15px' }} onClick={() => onSaveIdentity(selectedEntity.id, name, birthdate)}>
                    💾 Guardar Alterações
                  </button>
                </div>
              ) : (
                <p className="empty-state-light">Estruturas (Casas/Cactos) não possuem atributos editáveis.</p>
              )
            ) : (
              <p className="empty-state-light">Selecione uma entidade no cenário 3D.</p>
            )}
          </div>
        )}

        {/* === TERRENO SELECIONADO === */}
        {selectedTile && (
          <div className="card-panel">
            <div className="panel-header-flex">
              <h3 className="panel-title-light">Terreno Selecionado</h3>
              <button className="btn-close-light" onClick={onDeselectTile}>✕</button>
            </div>
            
            <div className="status-row">
              <span style={{color: '#94a3b8'}}>Tipo:</span> 
              <span className={`dot ${selectedTile.type === 'grass' ? 'green' : 'orange'}`}></span> 
              <span style={{fontWeight: 600}}>{selectedTile.type === 'grass' ? 'Grama Selvagem' : 'Terra Arada'}</span>
            </div>
            <div className="status-row">
              <span style={{color: '#94a3b8'}}>Coord:</span> 
              <span style={{fontWeight: 600, fontFamily: 'monospace'}}>X:{selectedTile.gridX} | Z:{selectedTile.gridZ}</span>
            </div>

            {selectedTile.type === 'grass' ? (
              <div style={{ marginTop: '20px' }}>
                <p style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px' }}>Deseja arar esta terra?</p>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button className="btn-light-action" style={{ background: '#dcfce7', color: '#059669' }} onClick={() => onPlow(selectedTile.id)}>✅ Sim</button>
                  <button className="btn-light-action" style={{ background: '#fee2e2', color: '#dc2626' }} onClick={onDeselectTile}>❌ Não</button>
                </div>
              </div>
            ) : (
              <div style={{ marginTop: '20px' }}>
                <p style={{ fontSize: '14px', fontWeight: 700, marginBottom: '10px' }}>Plantação ({selectedTile.crops.length}/2)</p>
                {selectedTile.crops.length < 2 ? (
                  <button className="btn-light-action" style={{ background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a' }} onClick={() => onPlant(selectedTile.id)}>
                    🥔 Plantar Batata
                  </button>
                ) : (
                  <div className="warning-box-light">
                    <span>⚠️</span> Capacidade máxima atingida.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}