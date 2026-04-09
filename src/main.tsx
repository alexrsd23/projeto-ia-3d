import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom' // <-- Importando o Router
import './index.css'
import App from './App.tsx'
import SurvivalDashboard from './components/layout/SurvivalDashboard.tsx' // <-- Importando o Painel

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        {/* A Rota Original (O Mundo 3D) */}
        <Route path="/" element={<App />} />
        
        {/* A Nova Rota (O Painel de Controle) */}
        <Route path="/painel/sobrevivencia" element={<SurvivalDashboard />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)