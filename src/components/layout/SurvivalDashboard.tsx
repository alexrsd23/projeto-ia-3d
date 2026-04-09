import { useState } from 'react';

export default function SurvivalDashboard() {
  const [activeTab, setActiveTab] = useState<'pessoas' | 'arvore' | 'profissoes' | 'ranking'>('pessoas');

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      
      {/* MENU LATERAL */}
      <div style={{ width: '250px', backgroundColor: '#1e293b', color: 'white', padding: '20px', display: 'flex', flexDirection: 'column' }}>
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
            🌳 Árvore Genética
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
            🏆 Ranking Social
          </button>
        </nav>
      </div>

      {/* ÁREA DE CONTEÚDO PRINCIPAL */}
      <div style={{ flexGrow: 1, padding: '30px', overflowY: 'auto' }}>
        
        {activeTab === 'pessoas' && (
          <div>
            <h1 style={{ fontSize: '24px', color: '#0f172a', marginBottom: '20px' }}>População Ativa</h1>
            <p style={{ color: '#64748b' }}>Aqui entrará o grid dinâmico com os cards de todos os bonecos vivos na simulação.</p>
            {/* Esqueleto do Grid que faremos no próximo passo */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '20px', marginTop: '20px' }}>
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0', textAlign: 'center', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
                <div style={{ fontSize: '40px', marginBottom: '10px' }}>👨‍🌾</div>
                <h3 style={{ margin: 0, color: '#334155' }}>Nome do Boneco</h3>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'arvore' && (
          <div>
            <h1 style={{ fontSize: '24px', color: '#0f172a', marginBottom: '20px' }}>Mapeamento Genético</h1>
            <p style={{ color: '#64748b' }}>Aqui renderizaremos as árvores de casamentos e descendentes (Ex: Família Bob & Mara).</p>
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
            <h1 style={{ fontSize: '24px', color: '#0f172a', marginBottom: '20px' }}>Auditoria Comportamental</h1>
            <p style={{ color: '#64748b' }}>Tabelas de reputação: Mais Confiáveis, Mentirosos e Neutros.</p>
          </div>
        )}

      </div>
    </div>
  );
}