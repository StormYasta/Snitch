import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  FileText, Clock, User, ExternalLink, ChevronDown,
  ChevronUp, CheckCircle, Info, ChevronRight, Tag, Vote
} from 'lucide-react';
import { getProposicao, getVotacaoVotos } from '../api/client';
import { Avatar } from '../components/Avatar';
import { VoteBadge, StatusBadge } from '../components/Badge';
import { DetailSkeleton } from '../components/Skeleton';
import type { VotacaoResumoItem } from '../types';

export const ProposicaoDetalhe: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const propId = Number(id);

  const { data: prop, isLoading, isError } = useQuery({
    queryKey: ['proposicao', propId],
    queryFn: () => getProposicao(propId),
    enabled: !isNaN(propId),
  });

  const [activeTab, setActiveTab] = useState<'tramitacao' | 'votacoes' | 'autores' | 'geral'>('geral');

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (isError || !prop) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-4">
        <h2 className="text-xl font-bold text-slate-800">Proposição não encontrada</h2>
        <p className="text-sm text-slate-500">
          Não foi possível carregar as informações desta proposição legislativa.
        </p>
        <Link
          to="/proposicoes"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-lg hover:bg-slate-800"
        >
          Voltar para listagem
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Topo do Detalhe da Proposição */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-xs space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                {prop.sigla_tipo} • Câmara dos Deputados
              </span>
              <StatusBadge situacao={prop.situacao || 'Em tramitação'} />
            </div>
            <h1 className="text-2xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
              {prop.sigla_tipo} {prop.numero}/{prop.ano}
            </h1>
          </div>

          {prop.url_inteiro_teor && (
            <a
              href={prop.url_inteiro_teor}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
            >
              <FileText className="w-4 h-4" />
              Ver Texto Integral (PDF)
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>

        {/* Ementa Oficial */}
        <div className="bg-slate-50 rounded-xl p-5 border border-slate-200">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
            Ementa Oficial
          </span>
          <p className="text-sm md:text-base text-slate-800 font-medium leading-relaxed">
            {prop.ementa}
          </p>
        </div>

        {/* Metadados rápidos */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t border-slate-100 text-xs">
          <div>
            <span className="text-slate-400 block mb-0.5">Apresentação</span>
            <span className="font-semibold text-slate-800">
              {prop.data_apresentacao ? prop.data_apresentacao.substring(0, 10) : 'Não informada'}
            </span>
          </div>

          <div>
            <span className="text-slate-400 block mb-0.5">Regime de Tramitação</span>
            <span className="font-semibold text-slate-800">{prop.regime || 'Ordinário'}</span>
          </div>

          <div>
            <span className="text-slate-400 block mb-0.5">Órgão Atual</span>
            <span className="font-semibold text-slate-800">{prop.orgao_atual || 'Plenário'}</span>
          </div>

          <div>
            <span className="text-slate-400 block mb-0.5">Autoria Principal</span>
            <span className="font-semibold text-slate-800">
              {prop.autores[0]?.nome_autor || 'Não informada'}
            </span>
          </div>
        </div>

        {/* Temas */}
        {prop.temas && prop.temas.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-2">
            <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center gap-1">
              <Tag className="w-3.5 h-3.5" /> Temas:
            </span>
            {prop.temas.map((t, i) => (
              <span key={i} className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Navegação por Abas */}
      <div className="flex border-b border-slate-200 text-sm font-medium gap-2">
        <button
          onClick={() => setActiveTab('geral')}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
            activeTab === 'geral'
              ? 'border-slate-900 text-slate-900'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Info className="w-4 h-4" />
          Visão Geral
        </button>

        <button
          onClick={() => setActiveTab('tramitacao')}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
            activeTab === 'tramitacao'
              ? 'border-slate-900 text-slate-900'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Clock className="w-4 h-4" />
          Tramitação ({prop.tramitacoes.length})
        </button>

        <button
          onClick={() => setActiveTab('votacoes')}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
            activeTab === 'votacoes'
              ? 'border-slate-900 text-slate-900'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Vote className="w-4 h-4" />
          Votações ({prop.votacoes.length})
        </button>

        <button
          onClick={() => setActiveTab('autores')}
          className={`pb-3 px-4 flex items-center gap-2 border-b-2 font-semibold transition-colors cursor-pointer ${
            activeTab === 'autores'
              ? 'border-slate-900 text-slate-900'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <User className="w-4 h-4" />
          Autores ({prop.autores.length})
        </button>
      </div>

      {/* ABA 1: VISÃO GERAL */}
      {activeTab === 'geral' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 md:p-8 space-y-6">
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-900">Ementa Detalhada</h3>
            <p className="text-sm text-slate-700 leading-relaxed">
              {prop.ementa_detalhada || prop.ementa || 'Nenhum detalhamento adicional registrado.'}
            </p>
          </div>

          {prop.despacho && (
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Despacho Inicial da Presidência</h3>
              <p className="text-sm text-slate-700 leading-relaxed font-mono bg-slate-50 p-4 rounded-lg border border-slate-200">
                {prop.despacho}
              </p>
            </div>
          )}

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Identificador oficial da Câmara: <strong>{prop.camara_id}</strong></span>
            {prop.uri && (
              <a href={prop.uri} target="_blank" rel="noreferrer" className="underline hover:text-slate-800 inline-flex items-center gap-1">
                Registro JSON oficial da API <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      )}

      {/* ABA 2: TRAMITAÇÃO (TIMELINE VERTICAL) */}
      {activeTab === 'tramitacao' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">Trajetória e Histórico de Tramitação</h3>
            <span className="text-xs text-slate-500">Registros oficiais em ordem cronológica</span>
          </div>

          <div className="relative pl-6 border-l-2 border-slate-200 space-y-8 ml-2">
            {prop.tramitacoes.map((tr) => (
              <div key={tr.id} className="relative group">
                {/* Marcador da timeline */}
                <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-white border-2 border-slate-800 group-hover:scale-125 transition-transform" />

                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">
                      {tr.data_hora ? tr.data_hora.substring(0, 10) : 'Data não informada'}
                    </span>
                    {tr.orgao && (
                      <span className="bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded text-[11px] border border-slate-200">
                        {tr.orgao}
                      </span>
                    )}
                    {tr.situacao && (
                      <span className="text-slate-500 text-xs italic">
                        • {tr.situacao}
                      </span>
                    )}
                  </div>

                  <h4 className="text-sm font-semibold text-slate-900">
                    {tr.descricao_tramitacao || 'Movimentação legislativa'}
                  </h4>

                  {tr.despacho && (
                    <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100 mt-2">
                      {tr.despacho}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ABA 3: VOTAÇÕES DA PROPOSIÇÃO */}
      {activeTab === 'votacoes' && (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-900 flex items-start gap-3">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <strong>Proveniência e Vínculos:</strong> Uma proposição pode possuir diversas votações ao longo de sua história (requerimentos de urgência, pareceres, substitutivos, destaques ou votação final). Os registros abaixo representam votações oficiais relacionadas a esta matéria.
            </div>
          </div>

          {prop.votacoes.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-sm text-slate-500">
              Nenhuma votação nominal registrada na base para esta proposição até o momento.
            </div>
          ) : (
            <div className="space-y-6">
              {prop.votacoes.map((v) => (
                <VotacaoCardAccordion key={v.id} votacao={v} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ABA 4: AUTORES */}
      {activeTab === 'autores' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 md:p-8 space-y-6">
          <h3 className="text-base font-bold text-slate-900">Autores e Coautores da Proposição</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {prop.autores.map((autor) => (
              <div
                key={autor.id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between gap-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Avatar src={autor.url_foto} name={autor.nome_autor} size="md" />
                  <div className="min-w-0">
                    <h4 className="text-sm font-bold text-slate-900 truncate">
                      {autor.nome_autor}
                    </h4>
                    <p className="text-xs text-slate-500">
                      {autor.sigla_partido ? `${autor.sigla_partido} - ${autor.uf}` : autor.tipo_autor || 'Autor'}
                    </p>
                    {autor.proponente && (
                      <span className="inline-block mt-1 text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                        Proponente Principal
                      </span>
                    )}
                  </div>
                </div>

                {autor.deputado_id && (
                  <Link
                    to={`/deputados/${autor.deputado_id}`}
                    className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
                    title="Ver perfil completo do deputado"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Componente de Accordion para cada votação da proposição
const VotacaoCardAccordion: React.FC<{ votacao: VotacaoResumoItem }> = ({ votacao }) => {
  const [expanded, setExpanded] = useState(false);
  const [filtroVoto, setFiltroVoto] = useState('');
  const [filtroPartido, setFiltroPartido] = useState('');
  const [filtroUf, setFiltroUf] = useState('');
  const [filtroBusca, setFiltroBusca] = useState('');

  const { data: votosData, isLoading } = useQuery({
    queryKey: ['votos', votacao.id, { filtroVoto, filtroPartido, filtroUf, filtroBusca }],
    queryFn: () => getVotacaoVotos(votacao.id, {
      voto: filtroVoto || undefined,
      partido: filtroPartido || undefined,
      uf: filtroUf || undefined,
      busca: filtroBusca || undefined,
      page: 1,
      page_size: 100
    }),
    enabled: expanded,
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Cabeçalho do Card */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-5 md:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer hover:bg-slate-50/80 transition-colors"
      >
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="font-semibold text-slate-700">
              {votacao.data_hora_registro ? votacao.data_hora_registro.substring(0, 10) : 'Data não informada'}
            </span>
            <span>•</span>
            <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">
              {votacao.orgao || 'PLEN'}
            </span>
            <span>•</span>
            <span className="italic text-slate-500">{votacao.tipo_relacao}</span>
          </div>

          <h4 className="text-sm md:text-base font-bold text-slate-900 leading-snug">
            {votacao.descricao}
          </h4>

          {votacao.resultado && (
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800">
              <CheckCircle className="w-3.5 h-3.5" />
              Resultado: {votacao.resultado}
            </div>
          )}
        </div>

        {/* Placar oficial e botão expandir */}
        <div className="flex items-center gap-6 self-end md:self-center shrink-0">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div className="bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded">
              <span className="text-[10px] text-emerald-700 block uppercase font-bold">Sim</span>
              <strong className="text-emerald-800 text-sm">{votacao.placar_sim}</strong>
            </div>
            <div className="bg-rose-50 border border-rose-200 px-2.5 py-1 rounded">
              <span className="text-[10px] text-rose-700 block uppercase font-bold">Não</span>
              <strong className="text-rose-800 text-sm">{votacao.placar_nao}</strong>
            </div>
            <div className="bg-amber-50 border border-amber-200 px-2.5 py-1 rounded">
              <span className="text-[10px] text-amber-700 block uppercase font-bold">Abst</span>
              <strong className="text-amber-800 text-sm">{votacao.placar_abstencao}</strong>
            </div>
            <div className="bg-purple-50 border border-purple-200 px-2.5 py-1 rounded">
              <span className="text-[10px] text-purple-700 block uppercase font-bold">Obst</span>
              <strong className="text-purple-800 text-sm">{votacao.placar_obstrucao}</strong>
            </div>
          </div>

          <div className="text-slate-400">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </div>
        </div>
      </div>

      {/* Conteúdo Expandido: Votos Nominais dos Parlamentares */}
      {expanded && (
        <div className="border-t border-slate-200 p-5 md:p-6 bg-slate-50/50 space-y-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <h5 className="text-sm font-bold text-slate-800">
              Votos Nominais dos Deputados ({votosData?.total || 0})
            </h5>

            {/* Filtros de Votos */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <input
                type="text"
                placeholder="Filtrar por nome..."
                value={filtroBusca}
                onChange={(e) => setFiltroBusca(e.target.value)}
                className="bg-white border border-slate-200 rounded-md px-2 py-1 text-xs"
              />
              <select
                value={filtroPartido}
                onChange={(e) => setFiltroPartido(e.target.value)}
                className="bg-white border border-slate-200 rounded-md px-2 py-1 text-xs"
              >
                <option value="">Todos os partidos</option>
                <option value="PT">PT</option>
                <option value="PL">PL</option>
                <option value="PP">PP</option>
                <option value="PSB">PSB</option>
                <option value="PSOL">PSOL</option>
                <option value="UNIÃO">UNIÃO</option>
                <option value="NOVO">NOVO</option>
                <option value="PDT">PDT</option>
                <option value="PCdoB">PCdoB</option>
              </select>
              <input
                type="text"
                placeholder="UF (ex: SP)"
                maxLength={2}
                value={filtroUf}
                onChange={(e) => setFiltroUf(e.target.value.toUpperCase())}
                className="bg-white border border-slate-200 rounded-md px-2 py-1 text-xs w-16 uppercase"
              />
              <select
                value={filtroVoto}
                onChange={(e) => setFiltroVoto(e.target.value)}
                className="bg-white border border-slate-200 rounded-md px-2 py-1 text-xs"
              >
                <option value="">Todos os votos</option>
                <option value="Sim">Sim</option>
                <option value="Não">Não</option>
                <option value="Abstenção">Abstenção</option>
                <option value="Obstrução">Obstrução</option>
                <option value="Artigo 17">Artigo 17</option>
              </select>
            </div>
          </div>

          {isLoading ? (
            <div className="py-6 text-center text-xs text-slate-500">Carregando votos nominais...</div>
          ) : !votosData?.items || votosData.items.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500 bg-white rounded-lg border border-slate-200">
              Nenhum voto correspondente aos filtros.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {votosData.items.map((v) => (
                <div
                  key={v.id}
                  className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs flex items-center justify-between gap-3"
                >
                  <Link
                    to={`/deputados/${v.deputado_id}`}
                    className="flex items-center gap-2.5 min-w-0 group"
                  >
                    <Avatar src={v.url_foto} name={v.nome_parlamentar} size="sm" />
                    <div className="min-w-0">
                      <span className="text-xs font-bold text-slate-900 group-hover:text-blue-600 truncate block">
                        {v.nome_parlamentar}
                      </span>
                      <span className="text-[11px] text-slate-500 block">
                        {v.sigla_partido} - {v.uf}
                      </span>
                    </div>
                  </Link>

                  <VoteBadge tipo={v.tipo_voto} size="sm" />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
