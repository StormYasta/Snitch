import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  FileText, Search, Filter, Calendar, Tag, User, ChevronLeft, ChevronRight
} from 'lucide-react';
import { getProposicoes } from '../api/client';
import { StatusBadge } from '../components/Badge';
import { CardSkeleton } from '../components/Skeleton';
import { EmptyState } from '../components/EmptyState';

export const Proposicoes: React.FC = () => {
  const [busca, setBusca] = useState('');
  const [tipo, setTipo] = useState('');
  const [ano, setAno] = useState<number | undefined>(undefined);
  const [situacao, setSituacao] = useState('');
  const [tema, setTema] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['proposicoes', { busca, tipo, ano, situacao, tema, page }],
    queryFn: () => getProposicoes({
      busca: busca.trim() || undefined,
      tipo: tipo || undefined,
      ano: ano || undefined,
      situacao: situacao || undefined,
      tema: tema || undefined,
      page,
      page_size: 9
    }),
  });

  const handleResetFilters = () => {
    setBusca('');
    setTipo('');
    setAno(undefined);
    setSituacao('');
    setTema('');
    setPage(1);
  };

  return (
    <div className="space-y-8">
      {/* Cabeçalho */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <FileText className="w-4 h-4" />
          Matérias Legislativas
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Proposições da Câmara dos Deputados
        </h1>
        <p className="text-slate-600 text-sm max-w-3xl">
          Consulte projetos de lei (PL), propostas de emenda à Constituição (PEC), medidas provisórias (MPV) e outras matérias oficiais em tramitação ou já aprovadas.
        </p>
      </div>

      {/* Barra de Filtros */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-800">
            <Filter className="w-4 h-4 text-slate-500" />
            Filtros de Pesquisa
          </div>
          {(busca || tipo || ano || situacao || tema) && (
            <button
              onClick={handleResetFilters}
              className="text-xs font-medium text-slate-500 hover:text-slate-900 underline cursor-pointer"
            >
              Limpar todos os filtros
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Busca textual */}
          <div className="relative sm:col-span-2">
            <input
              type="text"
              placeholder='Buscar por ementa, "PL 1234/2025"...'
              value={busca}
              onChange={(e) => { setBusca(e.target.value); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
          </div>

          {/* Tipo de Proposição */}
          <div>
            <select
              value={tipo}
              onChange={(e) => { setTipo(e.target.value); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <option value="">Todos os tipos (PL, PEC...)</option>
              <option value="PL">PL - Projeto de Lei</option>
              <option value="PEC">PEC - Proposta de Emenda</option>
              <option value="MPV">MPV - Medida Provisória</option>
              <option value="PLP">PLP - Lei Complementar</option>
              <option value="REQ">REQ - Requerimento</option>
            </select>
          </div>

          {/* Ano */}
          <div>
            <select
              value={ano || ''}
              onChange={(e) => { setAno(e.target.value ? Number(e.target.value) : undefined); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <option value="">Todos os anos</option>
              <option value="2026">2026</option>
              <option value="2025">2025</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2020">2020</option>
              <option value="2019">2019</option>
            </select>
          </div>

          {/* Tema */}
          <div>
            <select
              value={tema}
              onChange={(e) => { setTema(e.target.value); setPage(1); }}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              <option value="">Todos os temas</option>
              <option value="Saúde">Saúde</option>
              <option value="Economia">Economia & Tributação</option>
              <option value="Direitos Humanos">Direitos Humanos</option>
              <option value="Ciência, Tecnologia">Tecnologia & Inovação</option>
              <option value="Trabalho">Trabalho & Previdência</option>
              <option value="Administração Pública">Administração Pública</option>
            </select>
          </div>
        </div>
      </div>

      {/* Listagem de Proposições */}
      {isLoading ? (
        <CardSkeleton count={6} />
      ) : isError ? (
        <div className="p-8 text-center bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
          Ocorreu um erro ao carregar as proposições. Verifique a conexão com o backend.
        </div>
      ) : !data?.items || data.items.length === 0 ? (
        <EmptyState
          title="Nenhuma proposição encontrada"
          message="Nenhuma matéria corresponde aos filtros selecionados. Tente ajustar os parâmetros."
          actionText="Limpar filtros"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="space-y-6">
          <div className="text-xs text-slate-500 font-medium">
            Exibindo <span className="font-bold text-slate-800">{data.items.length}</span> de{' '}
            <span className="font-bold text-slate-800">{data.total}</span> proposições cadastradas
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {data.items.map((prop) => (
              <Link
                key={prop.id}
                to={`/proposicoes/${prop.id}`}
                className="group bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:border-slate-300 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-base text-slate-900 group-hover:text-blue-600 transition-colors">
                      {prop.sigla_tipo} {prop.numero}/{prop.ano}
                    </span>
                    <StatusBadge situacao={prop.situacao || 'Em tramitação'} />
                  </div>

                  <p className="text-xs md:text-sm text-slate-600 line-clamp-3 leading-relaxed">
                    {prop.ementa}
                  </p>

                  {/* Badges de tema */}
                  {prop.temas && prop.temas.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {prop.temas.map((t, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[11px] font-medium"
                        >
                          <Tag className="w-2.5 h-2.5 text-slate-400" />
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-4 mt-4 border-t border-slate-100 space-y-2 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5 truncate">
                    <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">
                      Autor: <strong className="text-slate-700 font-semibold">{prop.autor_principal || 'Não informado'}</strong>
                    </span>
                  </div>

                  {prop.data_apresentacao && (
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>Apresentação: {prop.data_apresentacao.substring(0, 10)}</span>
                    </div>
                  )}
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
