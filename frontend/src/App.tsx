import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { Home } from './pages/Home';
import { Proposicoes } from './pages/Proposicoes';
import { ProposicaoDetalhe } from './pages/ProposicaoDetalhe';
import { Deputados } from './pages/Deputados';
import { DeputadoPerfil } from './pages/DeputadoPerfil';
import { Governo } from './pages/Governo';
import { InstituicaoDetalhe } from './pages/InstituicaoDetalhe';
import { Fontes } from './pages/Fontes';
import { getStats } from './api/client';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutos
      retry: 1,
    },
  },
});

const AppContent: React.FC = () => {
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  });

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-10">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/proposicoes" element={<Proposicoes />} />
          <Route path="/proposicoes/:id" element={<ProposicaoDetalhe />} />
          <Route path="/deputados" element={<Deputados />} />
          <Route path="/deputados/:id" element={<DeputadoPerfil />} />
          <Route path="/governo" element={<Governo />} />
          <Route path="/governo/instituicoes/:id" element={<InstituicaoDetalhe />} />
          <Route path="/fontes" element={<Fontes />} />
        </Routes>
      </main>

      <Footer ultimaSincronizacao={stats?.ultima_sincronizacao} />
    </div>
  );
};

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
