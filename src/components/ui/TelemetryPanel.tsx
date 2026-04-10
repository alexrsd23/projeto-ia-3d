import { useState, useMemo, useRef, useEffect } from 'react';
import type { SimulationEvent, RouteAnalytics } from '../../types';
import SurvivalLogPanel from './SurvivalLogPanel'; // <-- Importando a Caixa-Preta!

interface TelemetryProps {
  events: SimulationEvent[];
  analytics: RouteAnalytics | null;
  currentMode: string; // <-- Recebendo o modo atual do App.tsx
}

export default function TelemetryPanel({ events, analytics, currentMode }: TelemetryProps) {
  const [activeTabRoutes, setActiveTabRoutes] = useState<'events' | 'routes' | 'ranking'>('events');

  const [hideCactusDeaths, setHideCactusDeaths] = useState(false);
  const [hideOutOfBounds, setHideOutOfBounds] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0; // Força a rolagem para o início (topo)
    }
  }, [events]);

  const filteredEvents = useMemo(() => {
    return events.filter(evt => {
      if (hideCactusDeaths && evt.message.includes('colidiu com um cacto')) return false;
      if (hideOutOfBounds && evt.message.includes('caiu da borda do mundo')) return false;
      return true;
    });
  }, [events, hideCactusDeaths, hideOutOfBounds]);

  return (
    <div className="light-telemetry-panel">
      <div className="telemetry-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Central de Inteligência</h2>
        <span style={{ fontSize: '11px', background: currentMode === 'SURVIVAL' ? '#10b981' : '#3b82f6', color: 'white', padding: '4px 8px', borderRadius: '12px', fontWeight: 'bold' }}>
          {currentMode === 'SURVIVAL' ? 'MODO ECOSSISTEMA' : 'MODO Q-LEARNING'}
        </span>
      </div>

      <div className="telemetry-content" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

        {/* === RENDERIZAÇÃO CONDICIONAL BASEADA NO MODO DO JOGO === */}

        {currentMode === 'SURVIVAL' ? (
          /* CAIXA PRETA DE SOBREVIVÊNCIA */
          <div style={{ flexGrow: 1, overflow: 'hidden' }}>
            <SurvivalLogPanel events={events} />
          </div>
        ) : (
          /* PAINEL ANTIGO DE ROTAS MANTIDO INTACTO */
          <>
            <div className="tab-nav-light">
              <button className={`tab-btn ${activeTabRoutes === 'events' ? 'active' : ''}`} onClick={() => setActiveTabRoutes('events')}>Log Agregado</button>
              <button className={`tab-btn ${activeTabRoutes === 'routes' ? 'active' : ''}`} onClick={() => setActiveTabRoutes('routes')}>Rotas Ótimas</button>
              <button className={`tab-btn ${activeTabRoutes === 'ranking' ? 'active' : ''}`} onClick={() => setActiveTabRoutes('ranking')}>Ranking</button>
            </div>

            <div className="log-container-light" style={{ flexGrow: 1 }}>
              {activeTabRoutes === 'events' && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
                    <button className={`card-btn ${hideCactusDeaths ? 'danger' : ''}`} style={{ padding: '10px 6px', flexDirection: 'row' }} onClick={() => setHideCactusDeaths(!hideCactusDeaths)}>
                      <span style={{ fontSize: '13px' }}>{hideCactusDeaths ? '🚫 Sem Cactos' : '🌵 Ocultar Cactos'}</span>
                    </button>
                    <button className={`card-btn ${hideOutOfBounds ? 'danger' : ''}`} style={{ padding: '10px 6px', flexDirection: 'row' }} onClick={() => setHideOutOfBounds(!hideOutOfBounds)}>
                      <span style={{ fontSize: '13px' }}>{hideOutOfBounds ? '🚫 Sem Quedas' : '🕳️ Ocultar Quedas'}</span>
                    </button>
                  </div>
                  {filteredEvents.length === 0 && <p className="empty-state-light">Aguardando eventos...</p>}

                  {/* ADICIONE O REF AQUI e garanta o overflow-y: auto */}
                  <div className="events-scroll-area" ref={scrollRef} style={{ overflowY: 'auto', height: '100%' }}>
                    {filteredEvents.map((evt, idx) => (
                      <div key={evt.id || idx} className={`log-entry-light ${evt.level.toLowerCase()}`}>
                        <span className="log-time-light">{evt.timestamp || new Date().toLocaleTimeString()}</span>
                        <span className="log-message-light">{evt.message}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {activeTabRoutes === 'routes' && ( /* Resto do código mantido */
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
                        {route.actions.map((act, i) => (<span key={i} className="route-action-pill">{act}</span>))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTabRoutes === 'ranking' && ( /* Resto do código mantido */
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
          </>
        )}
      </div>
    </div>
  );
}