import { useEffect, useRef, useState, useMemo } from 'react';
import type { SimulationEvent } from '../../types';

interface SurvivalLogPanelProps {
  events: SimulationEvent[];
}

// Adicionado o tipo 'broadcast' para as chamadas da rede global
type FilterKeys = 
  | 'genetic' | 'romance' | 'pursuit' | 'agriculture' 
  | 'plowing' | 'gate' | 'fence' | 'wandering' | 'waiting' | 'trade' | 'broadcast' | 'others';

export default function SurvivalLogPanel({ events }: SurvivalLogPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Estado dos filtros: APENAS 'trade' começa como true, 'broadcast' começa desativado
  const [filters, setFilters] = useState<Record<FilterKeys, boolean>>({
    genetic: false,
    romance: false,
    pursuit: false,
    agriculture: false,
    plowing: false,
    gate: false,
    fence: false,
    wandering: false,
    waiting: false,
    trade: true, // <--- ATIVO POR PADRÃO
    broadcast: false, // <--- NOVO: Desativado por padrão
    others: false, 
  });

  const toggleFilter = (key: FilterKeys) => {
    setFilters(prev => ({ ...prev, [key]: !prev[key] }));
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events]);

  const getMessageCategory = (msg: string): FilterKeys | 'uncategorized' => {
    const lowerMsg = msg.toLowerCase();
    
    // NOVO: Captura os "gritos" e comunicações do sistema global (Broadcast)
    if (lowerMsg.includes('sinal') || lowerMsg.includes('rádio') || lowerMsg.includes('s.o.s') || lowerMsg.includes('encomenda') || lowerMsg.includes('telecomunicação') || lowerMsg.includes('broadcast')) return 'broadcast';

    // Captura todas as transações comerciais e financeiras
    if (lowerMsg.includes('comprou') || lowerMsg.includes('pagou') || lowerMsg.includes('negocian') || lowerMsg.includes('plobs') || lowerMsg.includes('lote b2b') || lowerMsg.includes('mercado') || lowerMsg.includes('comprando') || lowerMsg.includes('vendeu') || lowerMsg.includes('investiu') || lowerMsg.includes('adquiriu')) return 'trade';

    if (lowerMsg.includes('tabu') || lowerMsg.includes('genétic')) return 'genetic';
    if (lowerMsg.includes('casamento') || lowerMsg.includes('filho') || lowerMsg.includes('romântico') || lowerMsg.includes('procreate') || lowerMsg.includes('romance') || lowerMsg.includes('flerte')) return 'romance';
    if (lowerMsg.includes('perseguindo') || lowerMsg.includes('fugindo') || lowerMsg.includes('farejou') || lowerMsg.includes('pânico')) return 'pursuit';
    if (lowerMsg.includes('colhendo') || lowerMsg.includes('semeando') || lowerMsg.includes('plantando') || lowerMsg.includes('batata') || lowerMsg.includes('colheita')) return 'agriculture';
    if (lowerMsg.includes('arando') || lowerMsg.includes('solo virgem')) return 'plowing';
    if (lowerMsg.includes('portão')) return 'gate';
    if (lowerMsg.includes('cerca') || lowerMsg.includes('murada')) return 'fence';
    if (lowerMsg.includes('vagando') || lowerMsg.includes('vagueando') || lowerMsg.includes('procurando') || lowerMsg.includes('explorando') || lowerMsg.includes('mapa') || lowerMsg.includes('mundo') || lowerMsg.includes('perdido')) return 'wandering';
    if (lowerMsg.includes('aguardando') || lowerMsg.includes('esperando') || lowerMsg.includes('hesitou') || lowerMsg.includes('parado')) return 'waiting';
    
    return 'uncategorized';
  };

  const filteredEvents = useMemo(() => {
    return events.filter(evt => {
      const category = getMessageCategory(evt.message);
      if (category === 'uncategorized') return filters.others; 
      return filters[category]; 
    });
  }, [events, filters]);

  const btnStyle = (isActive: boolean) => ({
    backgroundColor: isActive ? '#4a6b53' : '#2b2b2b',
    color: isActive ? '#ffffff' : '#888888',
    border: `1px solid ${isActive ? '#6a8759' : '#444'}`,
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    transition: 'all 0.2s',
  });

  return (
    <div style={{ backgroundColor: '#1e1e1e', borderRadius: '8px', border: '1px solid #333', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ backgroundColor: '#2d2d2d', padding: '8px 12px', borderBottom: '1px solid #111', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#a9b7c6', fontSize: '12px', fontWeight: 600, fontFamily: 'monospace' }}>
          TERMINAL_DE_AUDITORIA_BIOLÓGICA.exe
        </span>
        <span style={{ color: '#6a8759', fontSize: '10px' }}>🟢 SISTEMA ONLINE</span>
      </div>

      {/* Painel de Filtros */}
      <div style={{ backgroundColor: '#252525', padding: '8px', borderBottom: '1px solid #111', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
        <button style={btnStyle(filters.trade)} onClick={() => toggleFilter('trade')}>💰 Comércio</button>
        <button style={btnStyle(filters.broadcast)} onClick={() => toggleFilter('broadcast')}>📡 Broadcast</button>
        <button style={btnStyle(filters.genetic)} onClick={() => toggleFilter('genetic')}>🧬 Tabu Genético</button>
        <button style={btnStyle(filters.romance)} onClick={() => toggleFilter('romance')}>❤️ Romance</button>
        <button style={btnStyle(filters.pursuit)} onClick={() => toggleFilter('pursuit')}>🏃 Perseguição</button>
        <button style={btnStyle(filters.agriculture)} onClick={() => toggleFilter('agriculture')}>🌱 Agricultura</button>
        <button style={btnStyle(filters.plowing)} onClick={() => toggleFilter('plowing')}>🚜 Aração</button>
        <button style={btnStyle(filters.gate)} onClick={() => toggleFilter('gate')}>🚪 Portão</button>
        <button style={btnStyle(filters.fence)} onClick={() => toggleFilter('fence')}>🚧 Cerca</button>
        <button style={btnStyle(filters.wandering)} onClick={() => toggleFilter('wandering')}>🚶 Vagando</button>
        <button style={btnStyle(filters.waiting)} onClick={() => toggleFilter('waiting')}>⏳ Aguardando</button>
        <button style={btnStyle(filters.others)} onClick={() => toggleFilter('others')}>🗂️ Outros</button>
      </div>
      
      <div ref={scrollRef} style={{ padding: '12px', overflowY: 'auto', flexGrow: 1, fontFamily: '"Fira Code", monospace', fontSize: '12px', lineHeight: '1.6' }}>
        {filteredEvents.length === 0 && <p style={{ color: '#5c5c5c' }}>Painel silenciado. Ative os filtros acima para interceptar logs...</p>}
        
        {filteredEvents.map((evt, idx) => {
          let msgColor = '#a9b7c6'; 
          if (evt.level === 'WARNING') msgColor = '#e8bf6a'; 
          if (evt.level === 'ERROR') msgColor = '#cc666e'; 
          if (evt.level === 'SUCCESS') msgColor = '#6a8759'; 

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