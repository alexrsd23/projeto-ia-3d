interface InventoryCardProps {
  entityType: string;
  inventoryJSON?: string;
}

export default function InventoryCard({ entityType, inventoryJSON }: InventoryCardProps) {
  // ATUALIZADO: Todos os itens da macroeconomia incluídos nos defaults
  let items = { potatoes: 0, seeds: 0, logs: 0, stones: 0, fences: 0, gates: 0, metal_parts: 0, tree_seed: 0, plobs: 0 };
  
  try {
    if (inventoryJSON) {
      const parsed = JSON.parse(inventoryJSON);
      items = { ...items, ...parsed }; // Faz o merge seguro do que vier do Python
    }
  } catch (e) {
    console.error("Erro ao analisar o inventário", e);
  }

  return (
    <div style={{ background: '#fff', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
      <h4 style={{ fontSize: '12px', color: '#475569', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        🎒 Mochila / Inventário
      </h4>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        
        {/* === CONTA BANCÁRIA === */}
        <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: '8px', background: '#fef9c3', padding: '6px 10px', borderRadius: '6px', border: '1px solid #fde047' }}>
          <span style={{ fontSize: '16px' }}>💰</span>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '10px', color: '#854d0e', fontWeight: 600 }}>DINHEIRO (PLOBS)</span>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#713f12' }}>
              {typeof items.plobs === 'number' ? items.plobs.toFixed(2) : '0.00'}
            </span>
          </div>
        </div>

        {/* === ALIMENTAÇÃO BÁSICA (Todos) === */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f8fafc', padding: '6px 10px', borderRadius: '6px' }}>
          <span style={{ fontSize: '16px' }}>🥔</span>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 600 }}>BATATAS</span>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>{items.potatoes} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/16</span></span>
          </div>
        </div>
        
        {/* === INVENTÁRIO DO FAZENDEIRO === */}
        {(entityType === 'farmer' || entityType === 'character') && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f8fafc', padding: '6px 10px', borderRadius: '6px' }}>
            <span style={{ fontSize: '16px' }}>🌱</span>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 600 }}>SEMENTES</span>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>{items.seeds} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/16</span></span>
            </div>
          </div>
        )}

        {/* === INVENTÁRIO DO LENHADOR === */}
        {entityType === 'woodcutter' && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#fcf8f3', padding: '6px 10px', borderRadius: '6px', border: '1px solid #fde68a' }}>
              <span style={{ fontSize: '16px' }}>🪵</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#b45309', fontWeight: 600 }}>MADEIRA</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#78350f' }}>{items.logs} <span style={{fontSize:'10px', color:'#d4a373', fontWeight:400}}>/40</span></span>
              </div>
            </div>
            {/* O Lenhador carrega os Kits de Reflorestamento! */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#ecfdf5', padding: '6px 10px', borderRadius: '6px', border: '1px solid #a7f3d0' }}>
              <span style={{ fontSize: '16px' }}>🌲</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#047857', fontWeight: 600 }}>KITS PLANTIO</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#064e3b' }}>{items.tree_seed} <span style={{fontSize:'10px', color:'#6ee7b7', fontWeight:400}}>/20</span></span>
              </div>
            </div>
          </>
        )}

        {/* === INVENTÁRIO DO CONSTRUTOR === */}
        {entityType === 'builder' && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#fcf8f3', padding: '6px 10px', borderRadius: '6px', border: '1px solid #fde68a' }}>
              <span style={{ fontSize: '16px' }}>🪵</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#b45309', fontWeight: 600 }}>MADEIRA</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#78350f' }}>{items.logs} <span style={{fontSize:'10px', color:'#d4a373', fontWeight:400}}>/20</span></span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '16px' }}>🪨</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#475569', fontWeight: 600 }}>PEDRAS</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#334155' }}>{items.stones} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/16</span></span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '16px' }}>⚙️</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#475569', fontWeight: 600 }}>PEÇAS METAL</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#334155' }}>{items.metal_parts} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/10</span></span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '16px' }}>🧱</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#475569', fontWeight: 600 }}>CERCAS</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#334155' }}>{items.fences} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/20</span></span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '16px' }}>🚪</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#475569', fontWeight: 600 }}>PORTÕES</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#334155' }}>{items.gates} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/5</span></span>
              </div>
            </div>
          </>
        )}

        {/* === INVENTÁRIO DO FERREIRO === */}
        {entityType === 'blacksmith' && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '16px' }}>🪨</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#475569', fontWeight: 600 }}>MINÉRIOS</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#334155' }}>{items.stones} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/16</span></span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '16px' }}>⚙️</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#475569', fontWeight: 600 }}>ESTOQUE METAL</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#334155' }}>{items.metal_parts} <span style={{fontSize:'10px', color:'#94a3b8', fontWeight:400}}>/10</span></span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#ecfdf5', padding: '6px 10px', borderRadius: '6px', border: '1px solid #a7f3d0' }}>
              <span style={{ fontSize: '16px' }}>🌲</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '10px', color: '#047857', fontWeight: 600 }}>KITS PLANTIO</span>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#064e3b' }}>{items.tree_seed} <span style={{fontSize:'10px', color:'#6ee7b7', fontWeight:400}}>/20</span></span>
              </div>
            </div>
          </>
        )}

      </div>
    </div>
  );
}