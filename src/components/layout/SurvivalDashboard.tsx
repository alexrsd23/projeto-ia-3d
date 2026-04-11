import { useState, useEffect } from 'react';
import PolaroidAgentCard from '../ui/CharacterCards/PolaroidAgentCard';
import type { Entity } from '../../types';
import FamilyTreeViewport from '../ui/FamilyTreeViewport'; 

export default function SurvivalDashboard() {
  const [activeTab, setActiveTab] = useState<'pessoas' | 'arvore' | 'profissoes' | 'ranking'>('pessoas');
  const [agents, setAgents] = useState<Entity[]>([]);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/entities/survival_world');
        
        if (response.ok) {
          const data = await response.json();
          // Filtra apenas os agentes biológicos (exclui árvores, pedras, cercas, etc)
          const sentientTypes = ['farmer', 'woodcutter', 'builder', 'character'];
          const filteredAgents = data.filter((e: any) => sentientTypes.includes(e.type));
          setAgents(filteredAgents);
        }
      } catch (error) {
        console.error("Erro ao buscar agentes da colmeia:", error);
      }
    };

    // Busca imediata ao abrir a aba
    fetchAgents();
    
    // Atualiza silenciosamente a cada 3 segundos
    const intervalId = setInterval(fetchAgents, 3000);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      
      {/* MENU LATERAL */}
      <div style={{ width: '250px', backgroundColor: '#1e293b', color: 'white', padding: '20px', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '30px', color: '#38bdf8' }}>
          🧬 Painel de Controle<br/><span style={{ fontSize: '12px', color: '#94a3b8' }}>Simulação Evolutiva</span>
        </h2>
        
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button 
            onClick={() => setActiveTab('pessoas')}
            style={{ textAlign: 'left', padding: '10px 15px', borderRadius: '8px', border: 'none', cursor: 'pointer', backgroundColor: activeTab === 'pessoas' ? '#3b82f6' : 'transparent', color: activeTab === 'pessoas' ? 'white' : '#cbd5e1', transition: 'all 0.2s' }}
          >
            👥 Pessoas
          </button>
          <button 
            onClick={() => setActiveTab('arvore')}
            style={{ textAlign: 'left', padding: '10px 15px', borderRadius: '8px', border: 'none', cursor: 'pointer', backgroundColor: activeTab === 'arvore' ? '#3b82f6' : 'transparent', color: activeTab === 'arvore' ? 'white' : '#cbd5e1', transition: 'all 0.2s' }}
          >
            🌳 Árvore Genealógica
          </button>
          <button 
            onClick={() => setActiveTab('profissoes')}
            style={{ textAlign: 'left', padding: '10px 15px', borderRadius: '8px', border: 'none', cursor: 'pointer', backgroundColor: activeTab === 'profissoes' ? '#3b82f6' : 'transparent', color: activeTab === 'profissoes' ? 'white' : '#cbd5e1', transition: 'all 0.2s' }}
          >
            ⚒️ Profissões
          </button>
          <button 
            onClick={() => setActiveTab('ranking')}
            style={{ textAlign: 'left', padding: '10px 15px', borderRadius: '8px', border: 'none', cursor: 'pointer', backgroundColor: activeTab === 'ranking' ? '#3b82f6' : 'transparent', color: activeTab === 'ranking' ? 'white' : '#cbd5e1', transition: 'all 0.2s' }}
          >
            🏆 Ranking / Rotas
          </button>
        </nav>
      </div>

      {/* ÁREA DE CONTEÚDO PRINCIPAL */}
      <div style={{ flex: 1, padding: '40px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        
        {activeTab === 'pessoas' && (
          <div style={{ paddingBottom: '40px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h1 style={{ fontSize: '24px', color: '#0f172a', margin: 0 }}>Censo Populacional</h1>
              <span style={{ backgroundColor: '#e0f2fe', color: '#0369a1', padding: '6px 12px', borderRadius: '20px', fontSize: '14px', fontWeight: 600 }}>
                População Ativa: {agents.length}
              </span>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '20px', marginTop: '20px' }}>
              {agents.map(agent => (
                <div key={agent.id} style={{ display: 'flex', justifyContent: 'center' }}>
                  <PolaroidAgentCard entity={agent} />
                </div>
              ))}

              {agents.length === 0 && (
                <div style={{ gridColumn: '1 / -1', backgroundColor: 'white', padding: '40px', borderRadius: '12px', border: '1px solid #e2e8f0', textAlign: 'center', color: '#64748b' }}>
                  <div style={{ fontSize: '40px', marginBottom: '10px' }}>🌾</div>
                  <h3 style={{ margin: 0, color: '#334155' }}>O mundo está vazio.</h3>
                  <p>Inicie a simulação para gerar os primeiros habitantes.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'arvore' && (
          <div style={{ height: '100%', minHeight: '600px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginBottom: '20px' }}>
              <h1 style={{ fontSize: '24px', color: '#0f172a', margin: 0 }}>Mapeamento Genético Global</h1>
              <p style={{ color: '#64748b', margin: '5px 0 0 0' }}>
                A Grande Árvore da Vida. Faça scroll para dar zoom, clique e arraste para navegar por todos os cruzamentos do espaço-tempo.
              </p>
            </div>
            
            {/* O Container do React Flow (Visão Global Única) */}
            <div style={{ flex: 1, backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)' }}>
              <FamilyTreeViewport />
            </div>
          </div>
        )}

        {activeTab === 'profissoes' && (
          <div>
            <h1 style={{ fontSize: '24px', color: '#0f172a', marginBottom: '20px' }}>Divisão de Trabalho</h1>
            <p style={{ color: '#64748b' }}>Aqui colocaremos os dropdowns para filtrar Lenhadores, Plantadores, etc.</p>
          </div>
        )}

        {activeTab === 'ranking' && (
          <div>
            <h1 style={{ fontSize: '24px', color: '#0f172a', marginBottom: '20px' }}>Tabela de Classificação</h1>
            <p style={{ color: '#64748b' }}>Ranking de riqueza, idade e melhores rotas exploradas.</p>
          </div>
        )}

      </div>
    </div>
  );
}