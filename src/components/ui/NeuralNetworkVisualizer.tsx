import React from 'react';

interface NNProps {
  lastAction: number; // 0, 1, 2, 3
}

export default function NeuralNetworkVisualizer({ lastAction }: NNProps) {
  const actions = ["Frente", "Trás", "Esq", "Dir", "Diag CE", "Diag CD", "Diag BE", "Diag BD"];
  
  const inputs = Array.from({ length: 8 }, (_, i) => ({ id: `i${i}`, x: 30, y: 30 + i * 25 }));
  const hiddens = Array.from({ length: 4 }, (_, i) => ({ id: `h${i}`, x: 130, y: 70 + i * 35 }));
  const outputs = Array.from({ length: 8 }, (_, i) => ({ id: `o${i}`, x: 230, y: 20 + i * 25 }));

  return (
    <div className="nn-visualizer" style={{ 
      width: '320px', height: '300px', position: 'absolute', top: 20, left: 20, 
      background: 'rgba(0,0,0,0.85)', borderRadius: 8, padding: 10, 
      pointerEvents: 'none', zIndex: 10, border: '1px solid #333' 
    }}>
      <h4 style={{ color: 'white', margin: '5px 0 10px 0', fontSize: '13px', textAlign: 'center', letterSpacing: '1px' }}>
        AI BRAIN ACTIVITY
      </h4>
      
      <svg width="100%" height="220" style={{ overflow: 'visible' }}>
        
        {/* LINHAS: Camada de Entrada -> Oculta */}
        {inputs.map((inp, i) => 
          hiddens.map((hid, j) => {
            // Simulamos atividade visual na rede: algumas linhas acendem a laranja
            const isActive = (i + j + lastAction) % 4 === 0; 
            return (
              <line key={`ih-${i}-${j}`} x1={inp.x} y1={inp.y} x2={hid.x} y2={hid.y} 
                stroke={isActive ? 'rgba(230, 126, 34, 0.5)' : 'rgba(255,255,255,0.05)'} strokeWidth="1.5" />
            );
          })
        )}
        
        {/* LINHAS: Camada Oculta -> Saída (Ação Decidida) */}
        {hiddens.map((hid, j) => 
          outputs.map((out, k) => {
            const isFiring = k === lastAction; // Acende de vermelho as linhas que levam à ação escolhida
            return (
              <line key={`ho-${j}-${k}`} x1={hid.x} y1={hid.y} x2={out.x} y2={out.y} 
                stroke={isFiring ? 'rgba(255, 0, 0, 0.8)' : 'rgba(255,255,255,0.08)'} strokeWidth={isFiring ? "2" : "1"} />
            );
          })
        )}

        {/* NÓS DA REDE (Círculos) */}
        {inputs.map((inp, i) => <circle key={inp.id} cx={inp.x} cy={inp.y} r="6" fill={i % 2 === 0 ? "#e67e22" : "#333"} stroke="white" strokeWidth="1.5" />)}
        {hiddens.map(hid => <circle key={hid.id} cx={hid.x} cy={hid.y} r="8" fill="#111" stroke="white" strokeWidth="1.5" />)}
        
        {/* NÓS DE SAÍDA E TEXTO */}
        {outputs.map((out, k) => (
          <g key={out.id}>
            <circle cx={out.x} cy={out.y} r="8" 
              fill={k === lastAction ? "#ff0000" : "#111"} 
              stroke={k === lastAction ? "#ff0000" : "white"} 
              strokeWidth="2" 
              style={{ filter: k === lastAction ? 'drop-shadow(0 0 8px red)' : 'none' }} 
            />
            <text x={out.x + 15} y={out.y + 4} fill={k === lastAction ? "#00ff00" : "gray"} fontSize="12" fontFamily="monospace">
              {actions[k]}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}