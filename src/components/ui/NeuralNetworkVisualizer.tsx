import React from 'react';

interface NNProps {
  lastAction: number;
  qValues: number[];
  state: number[];
}

export default function NeuralNetworkVisualizer({ lastAction, qValues, state }: NNProps) {
  const actions = ["Frente", "Trás", "Esq", "Dir", "Diag CE", "Diag CD", "Diag BE", "Diag BD"];
  const inputLabels = ["Dist X", "Dist Z", "Inércia"];
  
  // A arquitetura real no PyTorch é 3 -> 64 -> 64 -> 8.
  // Visualmente, desenhamos 3 Entradas, 2 colunas de 6 nós (representando os 64x64 densos), e 8 Saídas.
  const inputs = Array.from({ length: 3 }, (_, i) => ({ id: `i${i}`, x: 30, y: 60 + i * 45 }));
  const hiddens1 = Array.from({ length: 6 }, (_, i) => ({ id: `h1_${i}`, x: 100, y: 30 + i * 30 }));
  const hiddens2 = Array.from({ length: 6 }, (_, i) => ({ id: `h2_${i}`, x: 170, y: 30 + i * 30 }));
  const outputs = Array.from({ length: 8 }, (_, i) => ({ id: `o${i}`, x: 240, y: 20 + i * 25 }));

  return (
    <div className="nn-visualizer" style={{ 
      width: '400px', height: '320px', position: 'absolute', top: 20, left: 20, 
      background: 'rgba(15, 23, 42, 0.95)', borderRadius: 12, padding: 15, 
      pointerEvents: 'none', zIndex: 10, border: '1px solid #334155',
      boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
    }}>
      <h4 style={{ color: '#f8fafc', margin: '0 0 5px 0', fontSize: '13px', textAlign: 'center', letterSpacing: '1px' }}>
        PYTORCH DQN: 3 ➔ 64 ➔ 64 ➔ 8
      </h4>
      <p style={{ color: '#94a3b8', fontSize: '10px', textAlign: 'center', margin: '0 0 15px 0'}}>Valores Analíticos em Tempo Real</p>
      
      <svg width="100%" height="240" style={{ overflow: 'visible' }}>
        
        {/* CONEXÕES (Simplificadas visualmente, mas representando a densidade) */}
        {inputs.map((inp) => 
          hiddens1.map((hid, j) => (
            <line key={`ih1-${inp.id}-${j}`} x1={inp.x} y1={inp.y} x2={hid.x} y2={hid.y} stroke="rgba(59, 130, 246, 0.15)" strokeWidth="1" />
          ))
        )}
        {hiddens1.map((h1) => 
          hiddens2.map((h2, j) => (
            <line key={`h1h2-${h1.id}-${j}`} x1={h1.x} y1={h1.y} x2={h2.x} y2={h2.y} stroke="rgba(139, 92, 246, 0.15)" strokeWidth="1" />
          ))
        )}
        {hiddens2.map((hid) => 
          outputs.map((out, k) => {
            const isWinner = k === lastAction;
            return (
              <line key={`ho-${hid.id}-${k}`} x1={hid.x} y1={hid.y} x2={out.x} y2={out.y} 
                stroke={isWinner ? 'rgba(16, 185, 129, 0.6)' : 'rgba(255,255,255,0.05)'} 
                strokeWidth={isWinner ? "2" : "1"} />
            );
          })
        )}

        {/* NÓS DE ENTRADA (ESTADOS REAIS: DISTÂNCIA X, DISTÂNCIA Z, INÉRCIA) */}
        {inputs.map((inp, i) => (
          <g key={inp.id}>
            <circle cx={inp.x} cy={inp.y} r="8" fill="#1e293b" stroke="#3b82f6" strokeWidth="2" />
            <text x={inp.x - 15} y={inp.y + 4} fill="#cbd5e1" fontSize="10" textAnchor="end">{inputLabels[i]}:</text>
            <text x={inp.x} y={inp.y + 22} fill="#3b82f6" fontSize="11" textAnchor="middle" fontWeight="bold">
              {state && state[i] !== undefined ? state[i].toFixed(0) : 0}
            </text>
          </g>
        ))}

        {/* CAMADAS OCULTAS (Representação dos 128 neurónios) */}
        {hiddens1.map(hid => <circle key={hid.id} cx={hid.x} cy={hid.y} r="5" fill="#334155" />)}
        {hiddens2.map(hid => <circle key={hid.id} cx={hid.x} cy={hid.y} r="5" fill="#334155" />)}
        
        {/* NÓS DE SAÍDA E Q-VALUES 100% REAIS */}
        {outputs.map((out, k) => {
          const isWinner = k === lastAction;
          // Mostra a nota (Q-Value) que o PyTorch deu a esta ação!
          const qVal = qValues && qValues[k] !== undefined ? qValues[k].toFixed(2) : "0.00";
          return (
            <g key={out.id}>
              <circle cx={out.x} cy={out.y} r="8" 
                fill={isWinner ? "#10b981" : "#1e293b"} 
                stroke={isWinner ? "#10b981" : "#64748b"} 
                strokeWidth="2" 
                style={{ filter: isWinner ? 'drop-shadow(0 0 6px #10b981)' : 'none' }} 
              />
              <text x={out.x + 15} y={out.y + 3} fill={isWinner ? "#10b981" : "#94a3b8"} fontSize="11" fontWeight={isWinner ? "bold" : "normal"}>
                {actions[k]}
              </text>
              <text x={out.x + 65} y={out.y + 3} fill={isWinner ? "#ffffff" : "#475569"} fontSize="10" fontFamily="monospace">
                (Q: {qVal})
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}