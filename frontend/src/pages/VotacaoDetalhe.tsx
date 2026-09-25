import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Calendar, ExternalLink, FileText, Search, Vote } from 'lucide-react';
import { getVotacao, getVotacaoVotos } from '../api/client';
import { Avatar } from '../components/Avatar';
import { VoteBadge } from '../components/Badge';
import { DetailSkeleton } from '../components/Skeleton';

const VOTO_OPTIONS = ['', 'Sim', 'Não', 'Abstenção', 'Obstrução'] as const;

export const VotacaoDetalhe: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const votacaoId = Number(id);
  const validId = Number.isSafeInteger(votacaoId) && votacaoId > 0;
  const [filtroVoto, setFiltroVoto] = useState('');
  const [busca, setBusca] = useState('');
  const [pagina, setPagina] = useState(1);

  const { data: votacao, isPending, isError } = useQuery({
    queryKey: ['votacao', votacaoId],
    queryFn: () => getVotacao(votacaoId),
    enabled: validId,
  });

  const { data: votos, isPending: votosLoading, isError: votosError } = useQuery({
    queryKey: ['votacaoVotos', votacaoId, filtroVoto, busca, pagina],
    queryFn: () => getVotacaoVotos(votacaoId, {
      voto: filtroVoto || undefined,
      busca: busca.trim() || undefined,
      page: pagina,
      page_size: 30,
    }),
    enabled: validId && !!votacao,
  });

  if (validId && isPending) return <DetailSkeleton />;
  if (!validId || isError || !votacao) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 space-y-4 text-center">
        <h1 className="text-xl font-bold">Votação não encontrada</h1>
        <p className="text-sm text-slate-600">O registro pode não ter sido sincronizado ou está indisponível.</p>
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900 hover:underline">
          <ArrowLeft className="w-4 h-4" /> Voltar à página inicial
        </Link>
      </div>
    );
  }

  const placar = [
    { label: 'Sim', value: votacao.placar_sim },
    { label: 'Não', value: votacao.placar_nao },
    { label: 'Abstenções', value: votacao.placar_abstencao },
    { label: 'Obstruções', value: votacao.placar_obstrucao },
  ];

  return (
    <div className="space-y-7">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900">
        <ArrowLeft className="w-4 h-4" /> Voltar às votações recentes
      </Link>

      <header className="bg-white border border-slate-200 rounded-2xl p-6 md:p-8 space-y-5">
        <div className="flex flex-wrap gap-3 items-center justify-between">
          <span className="text-xs uppercase tracking-wider font-bold text-slate-600 flex items-center gap-2">
            <Vote className="w-4 h-4" /> Votação da Câmara dos Deputados
          </span>
          {votacao.uri && (
            <a href={votacao.uri} rel="noreferrer" target="_blank"
              className="inline-flex gap-1.5 items-center text-xs font-semibold text-blue-700 hover:underline">
              Fonte oficial <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
        <h1 className="text-2xl font-bold leading-snug text-slate-900">{votacao.descricao}</h1>
        <div className="flex flex-wrap gap-3 items-center text-sm text-slate-600">
          <span className="inline-flex items-center gap-1.5">
            <Calendar className="w-4 h-4" />
            {votacao.data_hora_registro ? votacao.data_hora_registro.substring(0, 10) : 'Data não informada'}
          </span>
          <span>Órgão: {votacao.orgao || 'Não informado'}</span>
          <span>Registro: {votacao.camara_id}</span>
          <VoteBadge tipo={votacao.resultado || 'Resultado não informado'} />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {placar.map(({ label, value }) => (
            <div key={label} className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
              <div className="text-xs text-slate-600">{label}</div>
              <div className="text-2xl font-bold tabular-nums text-slate-900">{value}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500">
          Placar conforme os registros disponíveis na base. Zeros podem indicar campos não informados
          pela fonte; confira a votação oficial antes de interpretar a ausência de votos.
        </p>
      </header>

      {votacao.proposicoes.length > 0 && (
        <section className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
          <h2 className="text-base font-bold flex items-center gap-2">
            <FileText className="w-4 h-4" /> Proposições relacionadas
          </h2>
          <div className="flex flex-wrap gap-2">
            {votacao.proposicoes.map((p) => (
              <Link key={p.id} to={`/proposicoes/${p.id}`}
                className="text-sm font-medium border border-slate-200 hover:border-slate-400 rounded-lg px-3 py-2">
                {p.sigla_tipo} {p.numero}/{p.ano}
              </Link>
            ))}
          </div>
        </section>
      )}

      {votacao.orientacoes.length > 0 && (
        <section className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
          <h2 className="font-bold text-base">Orientações registradas pelas bancadas</h2>
          <div className="flex flex-wrap gap-2">
            {votacao.orientacoes.map((o) => (
              <div key={o.id} className="flex items-center gap-2 border border-slate-200 rounded-lg px-3 py-2 text-sm">
                <span className="font-semibold">{o.bancada}</span>
                <VoteBadge tipo={o.orientacao_voto} size="sm" />
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
        <div className="p-5 md:p-6 border-b border-slate-200 space-y-4">
          <h2 className="font-bold text-lg">Votos nominais registrados ({votacao.total_votos})</h2>
          <p className="text-xs text-slate-500">
            Apenas os registros sincronizados com a base oficial. A ausência de um parlamentar
            nesta lista não significa voto contrário nem ausência na sessão.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="relative">
              <span className="sr-only">Buscar parlamentar</span>
              <Search className="absolute w-4 h-4 text-slate-400 top-3 left-3 pointer-events-none" />
              <input type="search" value={busca} onChange={e => {setBusca(e.target.value);setPagina(1);}}
                placeholder="Buscar parlamentar..."
                className="w-full border border-slate-200 rounded-lg pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-700" />
            </label>
            <label>
              <span className="sr-only">Filtrar por voto</span>
              <select value={filtroVoto} onChange={e => {setFiltroVoto(e.target.value);setPagina(1);}}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm bg-white">
                {VOTO_OPTIONS.map(o => <option key={o} value={o}>{o || 'Todos os votos'}</option>)}
              </select>
            </label>
          </div>
        </div>
        {votosLoading ? (
          <div className="p-6 text-sm text-slate-500">Carregando registros nominais...</div>
        ) : votosError ? (
          <div className="p-6 text-sm text-rose-700">Não foi possível consultar os votos desta votação.</div>
        ) : !votos?.items.length ? (
          <div className="p-6 text-sm text-slate-500">Nenhum voto encontrado para estes filtros na base sincronizada.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {votos.items.map(v => (
              <Link to={`/deputados/${v.deputado_id}`} key={v.id}
                className="px-5 py-3 flex gap-3 items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <Avatar src={v.url_foto} name={v.nome_parlamentar} size="sm" />
                  <div className="min-w-0">
                    <div className="font-semibold text-sm text-slate-900 truncate">{v.nome_parlamentar}</div>
                    <div className="text-xs text-slate-500">
                      {v.sigla_partido_momento || v.sigla_partido || 'Sem partido informado'} / {v.uf_momento || v.uf || '-'}
                    </div>
                  </div>
                </div>
                <VoteBadge tipo={v.tipo_voto} size="sm" />
              </Link>
            ))}
          </div>
        )}
        {!!votos && votos.total_pages > 1 && (
          <nav className="px-5 py-4 border-t border-slate-200 flex gap-4 justify-between items-center text-sm" aria-label="Páginas de votos">
            <button disabled={pagina <= 1} onClick={() => setPagina(p => p-1)}
              className="px-3 py-2 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50">Anterior</button>
            <span className="text-slate-600 tabular-nums">{pagina} de {votos.total_pages}</span>
            <button disabled={pagina >= votos.total_pages} onClick={() => setPagina(p => p+1)}
              className="px-3 py-2 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50">Próxima</button>
          </nav>
        )}
      </section>
    </div>
  );
};
