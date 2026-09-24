import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Mail, Phone, MapPin, Calendar, Award,
  Info, TrendingUp, PieChart as PieIcon, History,
  ExternalLink, HelpCircle, ChevronRight, Vote
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip,
  Legend, PieChart, Pie, Cell
} from 'recharts';
import {
  getDeputado, getDeputadoAtividade, getDeputadoTemporal,
  getDeputadoDistribuicao, getDeputadoVotos, getDeputadoProposicoes,
  getDeputadoHistorico, getDeputadoTrajetoria
} from '../api/client';
import { Avatar } from '../components/Avatar';
import { VoteBadge, StatusBadge } from '../components/Badge';
import { DetailSkeleton } from '../components/Skeleton';

export const DeputadoPerfil: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const depId = Number(id);

  const [agrupamentoTemporal, setAgrupamentoTemporal] = useState<'mes' | 'ano'>('mes');
  const [activePropTab, setActivePropTab] = useState<'autoria' | 'votacao'>('autoria');
  const [filtroVoto, setFiltroVoto] = useState('');
  const [votosPage, setVotosPage] = useState(1);

  // Queries
  const { data: dep, isLoading: depLoading } = useQuery({
    queryKey: ['deputado', depId],
    queryFn: () => getDeputado(depId),
    enabled: !isNaN(depId),
  });

  const { data: atividade, isLoading: ativLoading } = useQuery({
    queryKey: ['deputadoAtividade', depId],
    queryFn: () => getDeputadoAtividade(depId),
    enabled: !isNaN(depId),
  });

  const { data: temporal } = useQuery({
    queryKey: ['deputadoTemporal', depId, agrupamentoTemporal],
    queryFn: () => getDeputadoTemporal(depId, agrupamentoTemporal),
    enabled: !isNaN(depId),
  });

  const { data: distribuicao } = useQuery({
    queryKey: ['deputadoDistribuicao', depId],
    queryFn: () => getDeputadoDistribuicao(depId),
    enabled: !isNaN(depId),
  });

  const { data: votosData } = useQuery({
    queryKey: ['deputadoVotos', depId, { filtroVoto, votosPage }],
    queryFn: () => getDeputadoVotos(depId, {
      tipo_voto: filtroVoto || undefined,
      page: votosPage,
      page_size: 8
    }),
    enabled: !isNaN(depId),
  });

  const { data: propsData } = useQuery({
    queryKey: ['deputadoProposicoes', depId, activePropTab],
    queryFn: () => getDeputadoProposicoes(depId, activePropTab, 1),
    enabled: !isNaN(depId),
  });

  const { data: historico } = useQuery({
    queryKey: ['deputadoHistorico', depId],
    queryFn: () => getDeputadoHistorico(depId),
    enabled: !isNaN(depId),
  });

  const { data: trajetoria } = useQuery({
    queryKey: ['deputadoTrajetoria', depId],
    queryFn: () => getDeputadoTrajetoria(depId),
    enabled: !isNaN(depId),
  });

  if (depLoading || ativLoading) {
    return <DetailSkeleton />;
  }

  if (!dep) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-4">
        <h2 className="text-xl font-bold text-slate-800">Deputado não encontrado</h2>
        <p className="text-sm text-slate-500">
          Não foi possível encontrar este parlamentar no sistema.
        </p>
        <Link
          to="/deputados"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-lg hover:bg-slate-800"
        >
          Voltar para listagem
        </Link>
      </div>
    );
  }

  // Cores neutras para gráfico de pizza de votos
  const PIE_COLORS: Record<string, string> = {
    'Sim': '#10b981',        // emerald
    'Não': '#f43f5e',        // rose
    'Abstenção': '#f59e0b',  // amber
    'Obstrução': '#a855f7',  // purple
    'Artigo 17': '#94a3b8',  // slate
  };

  return (
    <div className="space-y-10">
      {/* 9. CABEÇALHO DO PERFIL */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-xs">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <Avatar src={dep.url_foto} name={dep.nome_parlamentar} size="xl" className="ring-4 ring-slate-100 shadow-sm" />
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded">
                  {dep.sigla_partido} • {dep.uf}
                </span>
                <StatusBadge situacao={dep.situacao || 'Exercício'} />
                <span className="text-xs text-slate-400 font-medium">
                  {dep.legislatura}ª Legislatura
                </span>
              </div>

              <h1 className="text-2xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
                {dep.nome_parlamentar}
              </h1>

              {dep.nome_civil && dep.nome_civil !== dep.nome_parlamentar && (
                <p className="text-xs md:text-sm text-slate-500">
                  Nome civil: <strong className="font-medium text-slate-700">{dep.nome_civil}</strong>
                </p>
              )}
            </div>
          </div>

          {dep.uri && (
            <a
              href={dep.uri}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors self-start md:self-auto"
            >
              Registro Oficial na Câmara
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>

        {/* Informações Institucionais e Gabinete */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-8 pt-6 border-t border-slate-100 text-xs text-slate-600">
          <div className="flex items-start gap-2.5">
            <Mail className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-slate-400 block mb-0.5">E-mail Institucional</span>
              <span className="font-semibold text-slate-800 break-all">{dep.email || 'Não informado'}</span>
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-slate-400 block mb-0.5">Gabinete</span>
              <span className="font-semibold text-slate-800">
                {dep.gabinete?.predio ? `Prédio ${dep.gabinete.predio}, Sala ${dep.gabinete.sala || '-'}` : 'Não informado'}
              </span>
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <Phone className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-slate-400 block mb-0.5">Telefone</span>
              <span className="font-semibold text-slate-800">{dep.gabinete?.telefone || 'Não informado'}</span>
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <Calendar className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-slate-400 block mb-0.5">Naturalidade</span>
              <span className="font-semibold text-slate-800">
                {dep.municipio_nascimento ? `${dep.municipio_nascimento} (${dep.uf_nascimento || ''})` : 'Não informada'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 10. & 11. CARDS DE ATIVIDADE OBJETIVA */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Métricas Objetivas de Atividade</h2>
          <span className="text-xs text-slate-500">Calculado a partir de registros públicos oficiais</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {/* Votos Registrados */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Votos Registrados
            </span>
            <div className="text-2xl md:text-3xl font-extrabold text-slate-900">
              {atividade?.votos_registrados || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Total de votos nominais</p>
          </div>

          {/* Votações Distintas */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Votações Distintas
            </span>
            <div className="text-2xl md:text-3xl font-extrabold text-slate-900">
              {atividade?.votacoes_distintas || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Sessões de deliberação</p>
          </div>

          {/* DIAS COM ATIVIDADE REGISTRADA (Com Tooltip Explicativo) */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs relative group">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                Dias c/ Atividade
              </span>
              <div className="relative cursor-help" title={atividade?.nota_metodologica}>
                <HelpCircle className="w-3.5 h-3.5 text-slate-400 hover:text-slate-700" />
              </div>
            </div>
            <div className="text-2xl md:text-3xl font-extrabold text-slate-900">
              {atividade?.dias_com_atividade || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Datas únicas com registro</p>
          </div>

          {/* Presenças Registradas em Eventos */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Presenças em Eventos
            </span>
            <div className="text-2xl md:text-3xl font-extrabold text-slate-900">
              {atividade?.presencas_eventos || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Comissões, audiências e sessões</p>
          </div>

          {/* Proposições de Autoria/Coautoria */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Proposições de Autoria
            </span>
            <div className="text-2xl md:text-3xl font-extrabold text-slate-900">
              {atividade?.proposicoes_autoria || 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Como autor ou coautor</p>
          </div>
        </div>

        {/* Nota Metodológica Explicativa */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
          <span>
            <strong>Nota de transparência:</strong> {atividade?.nota_metodologica}
          </span>
        </div>
      </section>

      {/* 12. & 14. SEÇÃO DE GRÁFICOS: ATIVIDADE AO LONGO DO TEMPO E DISTRIBUIÇÃO DE VOTOS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Gráfico Temporal */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-slate-700" />
              <h3 className="text-base font-bold text-slate-900">Atividade ao Longo do Tempo</h3>
            </div>

            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs self-start sm:self-auto">
              <button
                onClick={() => setAgrupamentoTemporal('mes')}
                className={`px-3 py-1 rounded-md font-semibold transition-colors cursor-pointer ${
                  agrupamentoTemporal === 'mes' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Por Mês
              </button>
              <button
                onClick={() => setAgrupamentoTemporal('ano')}
                className={`px-3 py-1 rounded-md font-semibold transition-colors cursor-pointer ${
                  agrupamentoTemporal === 'ano' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Por Ano
              </button>
            </div>
          </div>

          <div className="h-64 w-full pt-4">
            {temporal && temporal.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={temporal} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="periodo" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    cursor={{ fill: '#f1f5f9' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Bar dataKey="votos" name="Votos Registrados" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="eventos" name="Presenças em Eventos" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="proposicoes" name="Proposições Apresentadas" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Nenhum dado temporal disponível para este período.
              </div>
            )}
          </div>
        </div>

        {/* 14. Distribuição de Votos */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4 flex flex-col justify-between">
          <div className="flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-slate-700" />
            <h3 className="text-base font-bold text-slate-900">Distribuição de Votos</h3>
          </div>

          <div className="h-48 w-full flex items-center justify-center">
            {distribuicao && distribuicao.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={distribuicao}
                    dataKey="quantidade"
                    nameKey="tipo_voto"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={3}
                  >
                    {distribuicao.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PIE_COLORS[entry.tipo_voto] || '#64748b'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-xs text-slate-400">Sem votos registrados</span>
            )}
          </div>

          {/* Legenda com percentuais */}
          <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs">
            {distribuicao?.map((item) => (
              <div key={item.tipo_voto} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: PIE_COLORS[item.tipo_voto] || '#64748b' }}
                  />
                  <span className="font-medium text-slate-700">{item.tipo_voto}</span>
                </div>
                <div className="text-slate-500 font-mono">
                  {item.quantidade} ({item.percentual}%)
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 13. HISTÓRICO DE VOTOS NOMINAIS */}
      <section className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Vote className="w-5 h-5 text-slate-700" />
            <h3 className="text-lg font-bold text-slate-900">Histórico de Votos Nominais</h3>
          </div>

          {/* Filtro por tipo de voto */}
          <div className="flex items-center gap-2">
            <select
              value={filtroVoto}
              onChange={(e) => { setFiltroVoto(e.target.value); setVotosPage(1); }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800"
            >
              <option value="">Todos os tipos de voto</option>
              <option value="Sim">Sim</option>
              <option value="Não">Não</option>
              <option value="Abstenção">Abstenção</option>
              <option value="Obstrução">Obstrução</option>
              <option value="Artigo 17">Artigo 17</option>
            </select>
          </div>
        </div>

        {votosData?.items && votosData.items.length > 0 ? (
          <div className="space-y-3">
            {votosData.items.map((v) => (
              <div
                key={v.id}
                className="p-4 rounded-xl border border-slate-200 hover:border-slate-300 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span className="font-semibold text-slate-700">
                      {v.data_hora ? v.data_hora.substring(0, 10) : 'Data não informada'}
                    </span>
                    {v.proposicao_sigla && (
                      <Link
                        to={`/proposicoes/${v.proposicao_id}`}
                        className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold px-2 py-0.5 rounded text-xs inline-flex items-center gap-1 transition-colors"
                      >
                        {v.proposicao_sigla} {v.proposicao_numero}/{v.proposicao_ano}
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                  <p className="text-sm font-medium text-slate-800 leading-snug">
                    {v.descricao_votacao}
                  </p>
                </div>

                <div className="self-end md:self-center shrink-0 text-right">
                  <VoteBadge tipo={v.tipo_voto} />
                  {(v.sigla_partido_momento || v.uf_momento) && (
                    <div className="text-[10px] text-slate-400 mt-1">
                      {v.sigla_partido_momento || 'Partido não informado'}
                      {v.uf_momento ? ` • ${v.uf_momento}` : ''}
                      {' '}na data do voto
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
            Nenhum voto registrado para este filtro.
          </div>
        )}
      </section>

      {/* 15. PROPOSIÇÕES RELACIONADAS AO DEPUTADO (AUTORIA vs VOTAÇÃO) */}
      <section className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-xs space-y-6">
        <div>
          <h3 className="text-lg font-bold text-slate-900 mb-1">Proposições Legislativas Relacionadas</h3>
          <p className="text-xs text-slate-500">
            Diferenciação clara entre proposições apresentadas oficialmente pelo parlamentar e aquelas em que apenas participou da votação.
          </p>
        </div>

        {/* Tabs de Autoria vs Votação */}
        <div className="flex border-b border-slate-200 gap-4 text-sm font-semibold">
          <button
            onClick={() => setActivePropTab('autoria')}
            className={`pb-3 border-b-2 transition-colors cursor-pointer flex items-center gap-2 ${
              activePropTab === 'autoria'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Award className="w-4 h-4" />
            Autoria / Coautoria Oficial
          </button>

          <button
            onClick={() => setActivePropTab('votacao')}
            className={`pb-3 border-b-2 transition-colors cursor-pointer flex items-center gap-2 ${
              activePropTab === 'votacao'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Vote className="w-4 h-4" />
            Participação em Votações
          </button>
        </div>

        {/* Lista de Proposições */}
        {propsData?.items && propsData.items.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {propsData.items.map((prop) => (
              <Link
                key={prop.id}
                to={`/proposicoes/${prop.id}`}
                className="group p-5 rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-xs transition-all flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-sm text-slate-900 group-hover:text-blue-600 transition-colors">
                      {prop.sigla_tipo} {prop.numero}/{prop.ano}
                    </span>
                    <StatusBadge situacao={prop.situacao || 'Em tramitação'} />
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                    {prop.ementa}
                  </p>
                </div>

                <div className="pt-3 mt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span>{activePropTab === 'autoria' ? 'Autor oficial' : 'Votado pelo parlamentar'}</span>
                  <span className="font-medium text-slate-700 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                    Abrir matéria <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
            Nenhuma proposição registrada nesta categoria.
          </div>
        )}
      </section>

      {/* 16. TRAJETÓRIA PARLAMENTAR */}
      {trajetoria && trajetoria.mandatos.length > 0 && (
        <section className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-xs space-y-5">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-slate-700" />
            <div>
              <h3 className="text-lg font-bold text-slate-900">Trajetória Parlamentar</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Mandatos preservados por legislatura; partido e UF são apresentados no contexto registrado para cada período.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {trajetoria.mandatos.map((m) => (
              <div key={m.id} className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-bold text-sm text-slate-900">
                    {m.legislatura_numero ? `${m.legislatura_numero}ª Legislatura` : m.cargo}
                  </div>
                  {m.sigla_partido && (
                    <span className="text-[11px] font-bold bg-white border border-slate-200 px-2 py-0.5 rounded">
                      {m.sigla_partido}{m.uf ? ` • ${m.uf}` : ''}
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-2">
                  {m.data_inicio ? m.data_inicio.substring(0, 10) : 'Início não informado'}
                  {' → '}
                  {m.data_fim ? m.data_fim.substring(0, 10) : 'atual'}
                </div>
                {m.situacao && <div className="text-xs text-slate-600 mt-2">{m.situacao}</div>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Registros detalhados fornecidos pelo endpoint histórico da Câmara */}
      {historico && historico.length > 0 && (
        <section className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-xs space-y-5">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-slate-700" />
            <h3 className="text-lg font-bold text-slate-900">Histórico de Mandato e Mudanças Partidárias</h3>
          </div>

          <div className="space-y-3">
            {historico.map((h) => (
              <div
                key={h.id}
                className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 flex items-center justify-between text-xs"
              >
                <div className="space-y-0.5">
                  <span className="font-bold text-slate-800">
                    {h.descricao_status || h.situacao || 'Registro oficial'}
                  </span>
                  <div className="text-slate-500">
                    Partido registrado: <strong>{h.sigla_partido || dep.sigla_partido}</strong> • {h.legislatura || dep.legislatura}ª Legislatura
                  </div>
                </div>
                <div className="text-slate-500 font-mono text-[11px]">
                  {h.data_hora ? h.data_hora.substring(0, 10) : 'Data oficial'}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
