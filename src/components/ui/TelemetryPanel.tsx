import { useState, useMemo } from 'react';
import type { SimulationEvent, RouteAnalytics } from '../../types';

interface TelemetryProps {
  events: SimulationEvent[];
  analytics: RouteAnalytics | null;
}

export default function TelemetryPanel({ events, analytics }: TelemetryProps) {
  const [activeTab, setActiveTab] = useState<'events' | 'routes' | 'ranking'>('events');
  
  // Lógica e estados mantidos rigorosamente iguais
  const [hideCactusDeaths, setHideCactusDeaths] = useState(false);
  const [hideOutOfBounds, setHideOutOfBounds] = useState(false);

  const filteredEvents = useMemo(() => {
    return events.filter(evt => {
      if (hideCactusDeaths && evt.message.includes('colidiu com um cacto')) return false;
      if (hideOutOfBounds && evt.message.includes('caiu da borda do mundo')) return false;
      return true;
    });
  }, [events, hideCactusDeaths, hideOutOfBounds]);

  return (
    <div className="light-telemetry-panel">
      <div className="telemetry-header">
        <h2>Terminal de Telemetria</h2>
      </div>
      
      <div className="telemetry-content">
        
        {/* NAVEGAÇÃO POR ABAS (TABS) MODERNAS */}
        <div className="tab-nav-light">
          <button className={`tab-btn ${activeTab === 'events' ? 'active' : ''}`} onClick={() => setActiveTab('events')}>Log</button>
          <button className={`tab-btn ${activeTab === 'routes' ? 'active' : ''}`} onClick={() => setActiveTab('routes')}>Rotas Ótimas</button>
          <button className={`tab-btn ${activeTab === 'ranking' ? 'active' : ''}`} onClick={() => setActiveTab('ranking')}>Ranking</button>
        </div>

        <div className="log-container-light">
          
          {/* TAB: EVENTOS */}
          {activeTab === 'events' && (
            <>
              {/* FILTROS NO ESTILO CARD */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
                <button 
                  className={`card-btn ${hideCactusDeaths ? 'danger' : ''}`} 
                  style={{ padding: '10px 6px', flexDirection: 'row' }}
                  onClick={() => setHideCactusDeaths(!hideCactusDeaths)}
                >
                  <span style={{ fontSize: '13px' }}>{hideCactusDeaths ? '🚫 Sem Cactos' : '🌵 Ocultar Cactos'}</span>
                </button>
                
                <button 
                  className={`card-btn ${hideOutOfBounds ? 'danger' : ''}`} 
                  style={{ padding: '10px 6px', flexDirection: 'row' }}
                  onClick={() => setHideOutOfBounds(!hideOutOfBounds)}
                >
                  <span style={{ fontSize: '13px' }}>{hideOutOfBounds ? '🚫 Sem Quedas' : '🕳️ Ocultar Quedas'}</span>
                </button>
              </div>

              {filteredEvents.length === 0 && <p className="empty-state-light">Aguardando eventos...</p>}
              
              <div className="events-scroll-area">
                {filteredEvents.map((evt) => (
                  <div key={evt.id} className={`log-entry-light ${evt.level.toLowerCase()}`}>
                    <span className="log-time-light">{new Date().toLocaleTimeString()}</span>
                    <span className="log-message-light">{evt.message}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* TAB: ROTAS ÓTIMAS (RouteMemory) */}
          {activeTab === 'routes' && (
            <div className="events-scroll-area">
              {!analytics?.bestRoutes.length && <p className="empty-state-light">Nenhuma rota validada ainda.</p>}
              {analytics?.bestRoutes.map((route, idx) => (
                <div key={idx} className="route-card-light">
                  <div className="route-card-header">
                    <span className="route-origin">Origem: {route.origin}</span>
                    <span className="route-steps">{route.steps} Ticks</span>
                  </div>
                  <p className="route-agent">Descobridor: <strong>{route.agent}</strong></p>
                  <div className="route-actions-container">
                    {route.actions.map((act, i) => (
                      <span key={i} className="route-action-pill">{act}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB: RANKING DE AGENTES */}
          {activeTab === 'ranking' && (
            <div className="events-scroll-area">
              {!analytics?.leaderboard.length && <p className="empty-state-light">O ranking está vazio.</p>}
              {analytics?.leaderboard.map((player, idx) => (
                <div key={idx} className="ranking-card-light">
                  <div className="ranking-medal">{idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '🏅'}</div>
                  <div className="ranking-info">
                    <p className="ranking-name">{player.name}</p>
                    <p className="ranking-stats">Sucessos: {player.successes} | Recorde: {player.bestTime} ticks</p>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}