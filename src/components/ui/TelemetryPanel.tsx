import { useState } from 'react';
import type { SimulationEvent, RouteAnalytics } from '../../types';

interface TelemetryProps {
  events: SimulationEvent[];
  analytics: RouteAnalytics | null;
}

export default function TelemetryPanel({ events, analytics }: TelemetryProps) {
  const [activeTab, setActiveTab] = useState<'events' | 'routes' | 'ranking'>('events');

  return (
    <div className="event-log-panel">
      <h3>Terminal de Telemetria</h3>
      
      <div style={{ display: 'flex', gap: '5px', marginBottom: '15px', borderBottom: '1px solid #3f4455', paddingBottom: '10px' }}>
        <button className={`btn-premium ${activeTab === 'events' ? 'btn-action' : 'btn-dark'}`} style={{padding: '6px', fontSize: '11px'}} onClick={() => setActiveTab('events')}>Log</button>
        <button className={`btn-premium ${activeTab === 'routes' ? 'btn-success' : 'btn-dark'}`} style={{padding: '6px', fontSize: '11px'}} onClick={() => setActiveTab('routes')}>Rotas Ótimas</button>
        <button className={`btn-premium ${activeTab === 'ranking' ? 'btn-warning' : 'btn-dark'}`} style={{padding: '6px', fontSize: '11px'}} onClick={() => setActiveTab('ranking')}>Ranking</button>
      </div>

      <div className="log-container">
        
        {/* TAB: EVENTOS */}
        {activeTab === 'events' && (
          <>
            {events.length === 0 && <p className="empty-state">Aguardando eventos...</p>}
            {events.map((evt) => (
              <div key={evt.id} className={`log-entry ${evt.level.toLowerCase()}`}>
                <span className="log-time">{new Date().toLocaleTimeString()}</span>
                <span className="log-message">{evt.message}</span>
              </div>
            ))}
          </>
        )}

        {/* TAB: ROTAS ÓTIMAS (RouteMemory) */}
        {activeTab === 'routes' && (
          <>
            {!analytics?.bestRoutes.length && <p className="empty-state">Nenhuma rota validada ainda.</p>}
            {analytics?.bestRoutes.map((route, idx) => (
              <div key={idx} style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '6px', marginBottom: '8px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#60a5fa', fontWeight: 'bold' }}>
                  <span>Origem: {route.origin}</span>
                  <span>{route.steps} Ticks</span>
                </div>
                <p style={{ margin: '5px 0', color: '#94a3b8' }}>Descobridor: <span style={{color: 'white'}}>{route.agent}</span></p>
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '5px' }}>
                  {route.actions.map((act, i) => (
                    <span key={i} style={{ background: '#2c313c', padding: '2px 6px', borderRadius: '4px', fontSize: '10px' }}>{act}</span>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}

        {/* TAB: RANKING DE AGENTES */}
        {activeTab === 'ranking' && (
          <>
            {!analytics?.leaderboard.length && <p className="empty-state">O ranking está vazio.</p>}
            {analytics?.leaderboard.map((player, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', background: 'rgba(241, 196, 15, 0.1)', border: '1px solid rgba(241, 196, 15, 0.3)', padding: '10px', borderRadius: '6px', marginBottom: '8px' }}>
                <span style={{ fontSize: '18px', marginRight: '10px' }}>{idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'}</span>
                <div style={{ flexGrow: 1 }}>
                  <p style={{ margin: 0, fontWeight: 'bold', fontSize: '13px', color: '#f1c40f' }}>{player.name}</p>
                  <p style={{ margin: 0, fontSize: '11px', color: '#cbd5e1' }}>Sucessos: {player.successes} | Melhor Tempo: {player.bestTime} ticks</p>
                </div>
              </div>
            ))}
          </>
        )}

      </div>
    </div>
  );
}