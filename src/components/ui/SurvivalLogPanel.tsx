import { useEffect, useRef } from 'react';
import type { SimulationEvent } from '../../types';

interface SurvivalLogPanelProps {
  events: SimulationEvent[];
}

export default function SurvivalLogPanel({ events }: SurvivalLogPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Força o scroll para o TOPO (onde estão os eventos mais recentes)
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events]);

  return (
    <div style={{ backgroundColor: '#1e1e1e', borderRadius: '8px', border: '1px solid #333', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ backgroundColor: '#2d2d2d', padding: '8px 12px', borderBottom: '1px solid #111', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#a9b7c6', fontSize: '12px', fontWeight: 600, fontFamily: 'monospace' }}>
          TERMINAL_DE_AUDITORIA_BIOLÓGICA.exe
        </span>
        <span style={{ color: '#6a8759', fontSize: '10px' }}>🟢 SISTEMA ONLINE</span>
      </div>
      
      <div ref={scrollRef} style={{ padding: '12px', overflowY: 'auto', flexGrow: 1, fontFamily: '"Fira Code", monospace', fontSize: '12px', lineHeight: '1.6' }}>
        {events.length === 0 && <p style={{ color: '#5c5c5c' }}>Aguardando inicialização do ecossistema...</p>}
        
        {events.map((evt, idx) => {
          // Cores baseadas na gravidade/tipo da ação
          let msgColor = '#a9b7c6'; // Padrão (Info)
          if (evt.level === 'WARNING') msgColor = '#e8bf6a'; // Avisos/Memória
          if (evt.level === 'ERROR') msgColor = '#cc666e'; // Mortes/Desespero
          if (evt.level === 'SUCCESS') msgColor = '#6a8759'; // Colheitas/Plantios

          return (
            <div key={evt.id || idx} style={{ display: 'flex', gap: '10px', marginBottom: '4px', borderBottom: '1px solid #2b2b2b', paddingBottom: '4px' }}>
              <span style={{ color: '#5c5c5c', minWidth: '65px' }}>{evt.timestamp || new Date().toLocaleTimeString()}</span>
              <span style={{ color: '#cc7832' }}>—</span>
              <span style={{ color: msgColor, wordBreak: 'break-word' }}>{evt.message}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}