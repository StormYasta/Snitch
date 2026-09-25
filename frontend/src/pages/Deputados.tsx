import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Users, Search, Filter,
  ChevronLeft, ChevronRight, ArrowUpDown
} from 'lucide-react';
import { getDeputados, getLegislaturas } from '../api/client';
import { Avatar } from '../components/Avatar';
import { StatusBadge } from '../components/Badge';
import { CardSkeleton } from '../components/Skeleton';
import { EmptyState } from '../components/EmptyState';

export const Deputados: React.FC = () => {
  const [busca, setBusca] = useState('');
  const [partido, setPartido] = useState('');
  const [uf, setUf] = useState('');
  const [situacao, setSituacao] = useState('');
  const [legislatura, setLegislatura] = useState('');
  const [ordem, setOrdem] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(1);

  const { data: legislaturas } = useQuery({
    queryKey: ['legislaturas'],
    queryFn: getLegislaturas,
  });

  const { data, isLoading, isError } = useQuery({
    queryKey: ['deputados', { busca, partido, uf, situacao, legislatura, ordem, page }],
    queryFn: () => getDeputados({
      busca: busca.trim() || undefined,
      partido: partido || undefined,
      uf: uf || undefined,
      situacao: situacao || undefined,
      legislatura: legislatura ? Number(legislatura) : undefined,
      ordenar_por: 'nome',
      ordem,
      page,
      page_size: 12
    }),
  });

  const handleResetFilters = () => {
    setBusca('');
    setPartido('');
    setUf('');
    setSituacao('');
    setLegislatura('');
    setOrdem('asc');
    setPage(1);
  };

  const estadosBrasil = [
    'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN',
    'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
  ];

  return (
    <div className="space-y-8">
      {/* Cabeçalho */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <Users className="w-4 h-4" />
          Parlamentares
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Deputados Federais
        </h1>
        <p className="text-slate-600 text-sm max-w-3xl">
          Consulte parlamentares atuais e históricos da Câmara dos Deputados, filtre por legislatura e acompanhe votos, autoria e trajetória parlamentar com dados oficiais.
        </p>
      </div>

      {/* Barra de Filtros */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-800">
            <Filter className="w-4 h-4 text-slate-500" />
            Filtros de Parlamentares
          </div>
          {(busca || partido || uf || situacao || legislatura) && (
            <button
              onClick={handleResetFilters}
              className="text-xs font-medium text-slate-500 hover:text-slate-900 underline cursor-pointer"
            >
              Limpar filtros
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {/* Busca textual */}
          <div className="relative sm:col-span-2">
            <input
              type="text"
              placeholder="Buscar por nome ou partido..."
              value={busca}
              onChange={(e) => { setBusca(e.target.value); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
          </div>

          {/* Partido */}
          <div>
            <select
              value={partido}
              onChange={(e) => { setPartido(e.target.value); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <option value="">Todos os partidos</option>
              <option value="PT">PT</option>
              <option value="PL">PL</option>
              <option value="PP">PP</option>
              <option value="UNIÃO">UNIÃO</option>
              <option value="PSD">PSD</option>
              <option value="MDB">MDB</option>
              <option value="PSB">PSB</option>
              <option value="PSOL">PSOL</option>
              <option value="PDT">PDT</option>
              <option value="NOVO">NOVO</option>
              <option value="PCdoB">PCdoB</option>
              <option value="REPUBLICANOS">REPUBLICANOS</option>
            </select>
          </div>

          {/* UF */}
          <div>
            <select
              value={uf}
              onChange={(e) => { setUf(e.target.value); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <option value="">Todos os estados (UF)</option>
              {estadosBrasil.map((e) => (
                <option key={e} value={e}>{e}</option>
              ))}
            </select>
          </div>

          {/* Legislatura */}
          <div>
            <select
              value={legislatura}
              onChange={(e) => { setLegislatura(e.target.value); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <option value="">Todas as legislaturas</option>
              {legislaturas?.map((leg) => (
                <option key={leg.id} value={leg.numero}>
                  {leg.numero}ª {leg.ano_inicio && leg.ano_fim ? `(${leg.ano_inicio}–${leg.ano_fim})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Ordenação Objetiva */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setOrdem(ordem === 'asc' ? 'desc' : 'asc')}
              className="w-full inline-flex items-center justify-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 cursor-pointer"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              Nome: {ordem === 'asc' ? 'A → Z' : 'Z → A'}
            </button>
          </div>
        </div>
      </div>

      {/* Listagem em Cards */}
      {isLoading ? (
        <CardSkeleton count={6} />
      ) : isError ? (
        <div className="p-8 text-center bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
          Ocorreu um erro ao carregar os deputados.
        </div>
      ) : !data?.items || data.items.length === 0 ? (
        <EmptyState
          title="Nenhum deputado encontrado"
          message="Nenhum parlamentar corresponde aos filtros aplicados."
          actionText="Limpar filtros"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="space-y-6">
          <div className="text-xs text-slate-500 font-medium">
            Exibindo <span className="font-bold text-slate-800">{data.items.length}</span> de{' '}
            <span className="font-bold text-slate-800">{data.total}</span> deputados
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {data.items.map((dep) => (
              <Link
                key={dep.id}
                to={`/deputados/${dep.id}`}
                className="group bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div className="space-y-4">
                  {/* Foto e Identificação */}
                  <div className="flex items-center gap-3.5">
                    <Avatar src={dep.url_foto} name={dep.nome_parlamentar} size="md" />
                    <div className="min-w-0 flex-1">
                      <h3 className="font-bold text-sm text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                        {dep.nome_parlamentar}
                      </h3>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-700">
                          {dep.sigla_partido || 'S/P'}
                        </span>
                        <span className="text-xs text-slate-500 font-medium">
                          {dep.uf}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2">
                    <StatusBadge situacao={dep.situacao || 'Exercício'} />
                  </div>

                  {/* Métricas objetivas resumidas */}
                  <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-center">
                    <div className="bg-slate-50 p-2 rounded-lg">
                      <span className="text-[10px] text-slate-400 block uppercase font-medium">Votos</span>
                      <strong className="text-xs font-bold text-slate-800">{dep.total_votos}</strong>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-lg">
                      <span className="text-[10px] text-slate-400 block uppercase font-medium">Eventos</span>
                      <strong className="text-xs font-bold text-slate-800">{dep.total_eventos}</strong>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-lg">
                      <span className="text-[10px] text-slate-400 block uppercase font-medium">Autoria</span>
                      <strong className="text-xs font-bold text-slate-800">{dep.total_proposicoes}</strong>
                    </div>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-100 text-xs font-semibold text-slate-700 group-hover:text-blue-600 transition-colors flex items-center justify-between">
                  <span>Ver perfil completo</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </Link>
            ))}
          </div>

          {/* Paginação */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg border border-slate-200 bg-white text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <span className="text-xs font-medium text-slate-600 px-3">
                Página <strong className="text-slate-900">{page}</strong> de{' '}
                <strong className="text-slate-900">{data.total_pages}</strong>
              </span>

              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="p-2 rounded-lg border border-slate-200 bg-white text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
