import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search, Users, FileText, CheckSquare, Vote, ArrowRight,
  TrendingUp, Calendar, ChevronRight, Network
} from 'lucide-react';
import { getStats, searchGlobal } from '../api/client';
import { Avatar } from '../components/Avatar';
import { VoteBadge, StatusBadge } from '../components/Badge';
import { CardSkeleton } from '../components/Skeleton';

export const Home: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryParam = searchParams.get('q') || '';
  const [searchQuery, setSearchQuery] = useState(queryParam);

  useEffect(() => {
    setSearchQuery(queryParam);
  }, [queryParam]);

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  });

  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['globalSearch', queryParam],
    queryFn: () => searchGlobal(queryParam),
    enabled: queryParam.trim().length > 0,
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      navigate('/');
    }
  };

  const isSearching = queryParam.trim().length > 0;

  return (
    <div className="space-y-12">
      {/* Hero Section com Busca Global */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white p-8 md:p-12 shadow-md">
        <div className="max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Dados Abertos da Câmara dos Deputados
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
            Acompanhe a atividade legislativa com clareza e transparência.
          </h1>

          <p className="text-slate-300 text-base md:text-lg leading-relaxed">
            Consulte a trajetória completa de proposições (PL, PEC, MPV), descubra como cada deputado votou e explore o histórico de atuação parlamentar com dados oficiais.
          </p>

          {/* Barra de Busca Global */}
          <form onSubmit={handleSearchSubmit} className="relative pt-2">
            <div className="relative flex items-center">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder='Pesquise por "PL 1234/2025", "PEC 45", ou nome do deputado (ex: "Tabata Amaral")...'
                className="w-full bg-white text-slate-900 pl-12 pr-28 py-3.5 rounded-xl shadow-lg text-sm md:text-base placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-slate-700 transition-all"
              />
              <Search className="w-5 h-5 text-slate-400 absolute left-4 pointer-events-none" />
              <button
                type="submit"
                className="absolute right-2 px-5 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition-colors cursor-pointer"
              >
                Buscar
              </button>
            </div>
          </form>

          {/* Dicas de busca */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span>Exemplos frequentes:</span>
            <button
              onClick={() => { setSearchQuery('PL 1234/2025'); navigate('/?q=PL%201234/2025'); }}
              className="px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              PL 1234/2025
            </button>
            <button
              onClick={() => { setSearchQuery('PEC 45/2019'); navigate('/?q=PEC%2045/2019'); }}
              className="px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              PEC 45/2019
            </button>
            <button
              onClick={() => { setSearchQuery('Tabata Amaral'); navigate('/?q=Tabata%20Amaral'); }}
              className="px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
            >
              Tabata Amaral
            </button>
          </div>
        </div>
      </section>

      {/* RESULTADOS DA BUSCA (quando há consulta ativa) */}
      {isSearching && (
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900">
              Resultados para: <span className="text-slate-600 font-normal">"{queryParam}"</span>
            </h2>
            <button
              onClick={() => { setSearchQuery(''); navigate('/'); }}
              className="text-xs font-medium text-slate-500 hover:text-slate-800 underline cursor-pointer"
            >
              Limpar busca
            </button>
          </div>

          {searchLoading ? (
            <CardSkeleton count={3} />
          ) : (
            <div className="space-y-8">
              {/* Proposições Encontradas */}
              {searchResults?.proposicoes && searchResults.proposicoes.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider">
                    <FileText className="w-4 h-4 text-slate-500" />
                    Proposições ({searchResults.proposicoes.length})
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {searchResults.proposicoes.map((p) => (
                      <Link
                        key={p.id}
                        to={`/proposicoes/${p.id}`}
                        className="group bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 hover:shadow-md transition-all flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-base text-slate-900 group-hover:text-blue-600 transition-colors">
                              {p.sigla_tipo} {p.numero}/{p.ano}
                            </span>
                            <StatusBadge situacao={p.situacao || 'Em tramitação'} />
                          </div>
                          <p className="text-sm text-slate-600 line-clamp-2">{p.ementa}</p>
                        </div>
                        <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                          <span>{p.autor_principal || 'Autor não informado'}</span>
                          <span className="inline-flex items-center gap-1 font-medium text-slate-700 group-hover:translate-x-0.5 transition-transform">
                            Ver detalhes <ChevronRight className="w-3.5 h-3.5" />
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Deputados Encontrados */}
              {searchResults?.deputados && searchResults.deputados.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider">
                    <Users className="w-4 h-4 text-slate-500" />
                    Deputados ({searchResults.deputados.length})
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {searchResults.deputados.map((d) => (
                      <Link
                        key={d.id}
                        to={`/deputados/${d.id}`}
                        className="group bg-white rounded-xl border border-slate-200 p-4 shadow-xs hover:border-slate-300 hover:shadow-md transition-all flex items-center gap-4"
                      >
                        <Avatar src={d.url_foto} name={d.nome_parlamentar} size="md" />
                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-sm text-slate-900 truncate group-hover:text-blue-600 transition-colors">
                            {d.nome_parlamentar}
                          </h4>
                          <p className="text-xs text-slate-500">
                            {d.sigla_partido} - {d.uf}
                          </p>
                          <span className="inline-block mt-1 text-[11px] font-medium text-slate-400">
                            {d.situacao || 'Exercício'}
                          </span>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Votações Encontradas */}
              {searchResults?.votacoes && searchResults.votacoes.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider">
                    <CheckSquare className="w-4 h-4 text-slate-500" />
                    Votações ({searchResults.votacoes.length})
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {searchResults.votacoes.map((v) => (
                      <div
                        key={v.id}
                        className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span>{v.data_hora_registro ? v.data_hora_registro.substring(0, 10) : 'Data não informada'}</span>
                            <span className="font-semibold text-slate-700">{v.orgao || 'PLEN'}</span>
                          </div>
                          <p className="text-sm font-medium text-slate-800 line-clamp-3">{v.descricao}</p>
                        </div>
                        <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                          <span className="font-semibold text-emerald-700">{v.resultado || 'Aprovado'}</span>
                          <span className="text-slate-500">
                            Sim: {v.placar_sim} | Não: {v.placar_nao}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(!searchResults?.proposicoes?.length && !searchResults?.deputados?.length && !searchResults?.votacoes?.length) && (
                <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
                  <p className="text-slate-600">Nenhum registro encontrado para "{queryParam}".</p>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Cards de Métricas Principais da Plataforma */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-sm transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Deputados</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">
            {statsLoading ? '...' : stats?.total_deputados || 0}
          </div>
          <p className="text-xs text-slate-500 mt-1">Parlamentares na base</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-sm transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Proposições</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">
            {statsLoading ? '...' : stats?.total_proposicoes || 0}
          </div>
          <p className="text-xs text-slate-500 mt-1">PL, PEC, MPV cadastradas</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-sm transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Votações</span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <CheckSquare className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">
            {statsLoading ? '...' : stats?.total_votacoes || 0}
          </div>
          <p className="text-xs text-slate-500 mt-1">Deliberações registradas</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-sm transition-shadow">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Votos Individuais</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Vote className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900">
            {statsLoading ? '...' : stats?.total_votos || 0}
          </div>
          <p className="text-xs text-slate-500 mt-1">Registros nominais auditados</p>
        </div>
      </section>

      {/* Os dois fluxos principais de navegação */}
      <section className="bg-slate-100/70 border border-slate-200 rounded-2xl p-6 md:p-8">
        <h3 className="text-lg font-bold text-slate-900 mb-2">Duas perspectivas principais de exploração</h3>
        <p className="text-sm text-slate-600 mb-6">Navegue pelas duas dimensões essenciais da atividade legislativa:</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wide bg-slate-100 px-3 py-1 rounded-md">
                Perspectiva da Proposição
              </div>
              <h4 className="text-base font-bold text-slate-900">
                PROPOSIÇÃO → VOTAÇÕES → DEPUTADOS
              </h4>
              <p className="text-sm text-slate-600 leading-relaxed">
                Consulte qualquer matéria legislativa (PL, PEC, MPV), acompanhe sua trajetória cronológica de tramitação e descubra o voto nominal de cada parlamentar.
              </p>
            </div>
            <Link
              to="/proposicoes"
              className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 hover:text-blue-600 transition-colors"
            >
              Explorar Proposições <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wide bg-slate-100 px-3 py-1 rounded-md">
                Perspectiva do Deputado
              </div>
              <h4 className="text-base font-bold text-slate-900">
                DEPUTADO → ATIVIDADE → VOTOS → PROPOSIÇÕES
              </h4>
              <p className="text-sm text-slate-600 leading-relaxed">
                Consulte o perfil parlamentar de qualquer deputado, analise a atividade ao longo do tempo em gráficos interativos e confira seu histórico completo de votos.
              </p>
            </div>
            <Link
              to="/deputados"
              className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-900 hover:text-blue-600 transition-colors"
            >
              Explorar Deputados <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <section className="rounded-2xl bg-slate-900 text-white p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="w-11 h-11 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-300">Nova dimensão</div>
            <h3 className="text-xl font-bold mt-1">Entenda o Governo</h3>
            <p className="text-sm text-slate-300 mt-2 max-w-2xl">
              Explore como União, estados, municípios, Poderes e instituições públicas se relacionam e conecte a Câmara diretamente aos dados legislativos.
            </p>
          </div>
        </div>
        <Link
          to="/governo"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-white text-slate-900 text-sm font-bold hover:bg-slate-100 shrink-0"
        >
          Explorar estrutura <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      {/* Grid com Votações Recentes e Proposições Movimentadas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Votações Recentes */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-slate-700" />
              <h3 className="text-lg font-bold text-slate-900">Votações Recentes</h3>
            </div>
          </div>

          <div className="space-y-3">
            {statsLoading ? (
              <CardSkeleton count={2} />
            ) : (
              stats?.votacoes_recentes?.map((v) => (
                <div
                  key={v.id}
                  className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3"
                >
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {v.data_hora_registro ? v.data_hora_registro.substring(0, 10) : 'Data oficial'}
                    </span>
                    <span className="font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                      {v.orgao || 'PLEN'}
                    </span>
                  </div>

                  <p className="text-sm font-medium text-slate-800 leading-relaxed">
                    {v.descricao}
                  </p>

                  <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <VoteBadge tipo={v.resultado || 'Aprovada'} size="sm" />
                      <span className="text-slate-500 text-[11px] italic">
                        {v.tipo_relacao}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-slate-600 font-medium text-[11px]">
                      <span className="text-emerald-700">Sim: {v.placar_sim}</span>
                      <span className="text-rose-700">Não: {v.placar_nao}</span>
                      {v.placar_abstencao > 0 && <span className="text-amber-700">Abst: {v.placar_abstencao}</span>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Proposições Movimentadas */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-slate-700" />
              <h3 className="text-lg font-bold text-slate-900">Proposições em Destaque</h3>
            </div>
            <Link to="/proposicoes" className="text-xs font-semibold text-slate-600 hover:text-slate-900">
              Ver todas →
            </Link>
          </div>

          <div className="space-y-3">
            {statsLoading ? (
              <CardSkeleton count={2} />
            ) : (
              stats?.proposicoes_recentes?.map((p) => (
                <Link
                  key={p.id}
                  to={`/proposicoes/${p.id}`}
                  className="group block bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 hover:shadow-sm transition-all space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-base text-slate-900 group-hover:text-blue-600 transition-colors">
                      {p.sigla_tipo} {p.numero}/{p.ano}
                    </span>
                    <StatusBadge situacao={p.situacao || 'Em tramitação'} />
                  </div>

                  <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed">
                    {p.ementa}
                  </p>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <div className="flex flex-wrap gap-1.5">
                      {p.temas.slice(0, 2).map((t, idx) => (
                        <span key={idx} className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[11px]">
                          {t}
                        </span>
                      ))}
                    </div>
                    <span className="font-medium text-slate-700 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                      Acompanhar <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
};
