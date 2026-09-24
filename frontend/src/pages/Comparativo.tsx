import { useMemo, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import {
  ChevronLeft, ChevronRight, ExternalLink, GitCompareArrows,
  Info, Search, Share2, X,
} from 'lucide-react';
import {
  PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart,
  ResponsiveContainer, Tooltip,
} from 'recharts';
import {
  getComparativo, getComparativoVotacoes, getDeputado,
  getDeputadoIndicadores, getDeputados, getLegislaturas,
} from '../api/client';
import { Avatar } from '../components/Avatar';
import type {
  ComparativoDeputado, ComparativoFiltro, ComparativoParlamentar,
  DeputadoIndicadores,
} from '../types';

const currentYear = new Date().getFullYear();
const currentMonth = new Date().getMonth() + 1;
const palette = ['#2563eb', '#7c3aed', '#0f766e'];
const prettyNumber = (v: number | null | undefined) =>
  v == null ? '—' : new Intl.NumberFormat('pt-BR').format(v);
const prettyPercent = (v: number | null | undefined) =>
  v == null ? '—' : `${v.toFixed(1)}%`;
const prettyMoney = (v: number | null | undefined) =>
  v == null ? '—' : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);

function Selector({
  slot, selected, taken, pick, remove,
}: {
  slot: number;
  selected?: ComparativoParlamentar;
  taken: number[];
  pick: (id: number) => void;
  remove: () => void;
}) {
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState(false);
  const term = search.trim();
  const { data, isFetching } = useQuery({
    queryKey: ['comparar-selecionar', term],
    queryFn: () => getDeputados({ busca: term, page_size: 25 }),
    enabled: editing && term.length >= 2,
    staleTime: 60000,
  });
  const results = (data?.items || []).filter((dep) => !taken.includes(dep.id));

  return (
    <div className="relative min-w-0 rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        <span>Parlamentar {slot + 1}</span>
        {selected && (
          <button type="button" onClick={remove} aria-label="Remover parlamentar"
            className="rounded-md p-1 text-slate-500 hover:bg-slate-100">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
      {selected && !editing ? (
        <button type="button" onClick={() => setEditing(true)}
          className="flex w-full items-center gap-3 text-left">
          <Avatar src={selected.url_foto || undefined}
            name={selected.nome_parlamentar} size="md" />
          <span className="min-w-0">
            <strong className="block truncate text-sm text-slate-900">
              {selected.nome_parlamentar}
            </strong>
            <span className="block text-xs text-slate-500">
              {selected.sigla_partido || 'S/P'} · {selected.uf || '—'}
            </span>
            <span className="text-[11px] font-semibold text-blue-700">Trocar</span>
          </span>
        </button>
      ) : (
        <div className="relative">
          <label className="sr-only" htmlFor={`comparar-search-${slot}`}>Buscar parlamentar</label>
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input id={`comparar-search-${slot}`} type="search" value={search}
            autoComplete="off" onFocus={() => setEditing(true)}
            onChange={(event) => { setSearch(event.target.value); setEditing(true); }}
            placeholder={selected ? 'Buscar substituto...' : 'Buscar por nome...'}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-2 text-sm outline-none focus:border-slate-400" />
          {editing && (
            <div className="absolute left-0 right-0 top-full z-30 mt-1 max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl">
              {term.length < 2 ? (
                <p className="px-3 py-3 text-xs text-slate-500">Digite pelo menos duas letras.</p>
              ) : isFetching ? (
                <p className="px-3 py-3 text-xs text-slate-500">Buscando...</p>
              ) : results.length ? results.map((item) => (
                <button key={item.id} type="button"
                  onClick={() => { pick(item.id); setSearch(''); setEditing(false); }}
                  className="flex w-full items-center gap-2 border-b border-slate-100 px-3 py-2.5 text-left last:border-0 hover:bg-slate-50">
                  <Avatar src={item.url_foto} name={item.nome_parlamentar} size="sm" />
                  <span className="min-w-0">
                    <strong className="block truncate text-xs text-slate-900">{item.nome_parlamentar}</strong>
                    <span className="block text-[11px] text-slate-500">
                      {item.sigla_partido || 'S/P'} · {item.uf || '—'}
                    </span>
                  </span>
                </button>
              )) : <p className="px-3 py-3 text-xs text-slate-500">Nenhum parlamentar encontrado.</p>}
              <button type="button" onClick={() => { setEditing(false); setSearch(''); }}
                className="w-full border-t border-slate-100 px-3 py-2 text-left text-xs text-slate-500 hover:bg-slate-50">
                Fechar busca
              </button>
            </div>
          )}
        </div>
      )}
      {!selected && <p className="mt-2 text-[11px] text-slate-400">
        {slot === 2 ? 'Terceiro parlamentar (opcional)' : 'Selecione para comparar'}
      </p>}
    </div>
  );
}

interface DataRow {
  label: string;
  hint?: string;
  values: ReactNode[];
}

function MetricTable({
  title, subtitle, deputies, rows,
}: {
  title: string;
  subtitle: string;
  deputies: ComparativoDeputado[];
  rows: DataRow[];
}) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-lg font-bold text-slate-900">{title}</h2>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">{subtitle}</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px] table-fixed text-left">
          <thead className="bg-slate-50 text-xs font-semibold text-slate-600">
            <tr>
              <th className="w-[230px] px-5 py-3">Indicador</th>
              {deputies.map((item) => (
                <th key={item.deputado.id} className="px-4 py-3">{item.deputado.nome_parlamentar}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-t border-slate-100">
                <th scope="row" className="px-5 py-3 text-xs font-medium text-slate-600">
                  {row.label}
                  {row.hint && <small className="mt-1 block text-[10px] text-slate-400">{row.hint}</small>}
                </th>
                {row.values.map((value, index) => (
                  <td key={deputies[index].deputado.id} className="px-4 py-3 text-sm font-bold text-slate-900">
                    {value}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function IndicatorSection({
  deputies, indicators, pending, ano, mes,
}: {
  deputies: ComparativoDeputado[];
  indicators: Record<number, DeputadoIndicadores | null>;
  pending: boolean;
  ano: number;
  mes: number;
}) {
  const makeRow = (
    label: string, field: keyof DeputadoIndicadores,
    formatter: (v: number | null | undefined) => string = prettyNumber, hint?: string
  ): DataRow => ({
    label, hint,
    values: deputies.map((item) => {
      const id = item.deputado.id;
      if (pending && !(id in indicators)) return '…';
      const source = indicators[id];
      return source ? formatter(source[field] as number | null | undefined) : '—';
    }),
  });
  return (
    <MetricTable title="Indicadores legislativos"
      subtitle={`PLs e votações: ${ano}. Presença e cota: ${String(mes).padStart(2, '0')}/${ano}.`}
      deputies={deputies}
      rows={[
        makeRow('Presença no Plenário', 'percentual_presenca', prettyPercent),
        makeRow('Presenças no Plenário', 'presencas_plenario'),
        makeRow('Faltas', 'faltas_plenario'),
        makeRow('Faltas justificadas', 'faltas_justificadas'),
        makeRow('Faltas não justificadas', 'faltas_nao_justificadas'),
        makeRow('PLs apresentados', 'pls_apresentados'),
        makeRow('PLs aprovados (situação registrada)', 'pls_aprovados'),
        makeRow('Taxa de aprovação registrada', 'percentual_pls_aprovados', prettyPercent,
          'Entre os PLs apresentados no ano, conforme situação na base local'),
        makeRow('Uso da cota (valor líquido)', 'uso_cota_mes', prettyMoney),
        makeRow('Votações nominais registradas', 'votacoes_nominais'),
      ]}
    />
  );
}

const activityFields = [
  ['votos_registrados', 'Votos registrados'],
  ['votacoes_distintas', 'Votações distintas'],
  ['dias_com_atividade', 'Dias com atividade registrada'],
  ['presencas_eventos', 'Participações em eventos'],
  ['proposicoes_autoria', 'Proposições de autoria'],
] as const;

function ActivitySection({ deputies }: { deputies: ComparativoDeputado[] }) {
  return (
    <MetricTable title="Métricas objetivas de atividade"
      subtitle="Contagens do mesmo ano selecionado; os registros não representam toda a atividade profissional."
      deputies={deputies}
      rows={activityFields.map(([key, label]) => {
        const max = Math.max(1, ...deputies.map((entry) => entry.atividade[key]));
        return {
          label,
          values: deputies.map((entry, index) => (
            <div key={entry.deputado.id} className="space-y-1.5">
              <span>{prettyNumber(entry.atividade[key])}</span>
              <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full" style={{
                  width: `${entry.atividade[key] / max * 100}%`, background: palette[index],
                }} />
              </div>
            </div>
          )),
        };
      })}
    />
  );
}

function VoteSection({ deputies }: { deputies: ComparativoDeputado[] }) {
  const fields = [
    ['sim', 'Sim'], ['nao', 'Não'], ['abstencao', 'Abstenção'],
    ['obstrucao', 'Obstrução'], ['outros', 'Outros'],
  ] as const;
  return (
    <MetricTable title="Distribuição dos votos nominais"
      subtitle="Contagens literais; abstenção, obstrução e outros não são contabilizados como voto Não."
      deputies={deputies}
      rows={fields.map(([key, label]) => ({
        label, values: deputies.map((entry) => prettyNumber(entry.votos[key])),
      }))}
    />
  );
}

function ThemeSection({ deputies }: { deputies: ComparativoDeputado[] }) {
  const [selectedVote, setSelectedVote] = useState<'sim' | 'nao'>('sim');
  const themes = useMemo(() => {
    const combined = new Map<number, { id: number; nome: string; n: number }>();
    deputies.forEach((entry) => entry.temas.forEach((theme) => {
      const previous = combined.get(theme.id);
      combined.set(theme.id, {
        id: theme.id, nome: theme.nome,
        n: (previous?.n || 0) + theme.total_sim_nao,
      });
    }));
    return [...combined.values()].filter((theme) => theme.n > 0)
      .sort((a, b) => b.n - a.n || a.nome.localeCompare(b.nome, 'pt-BR')).slice(0, 8);
  }, [deputies]);

  const pickTheme = (deputyId: number, themeId: number) =>
    deputies.find((entry) => entry.deputado.id === deputyId)
      ?.temas.find((theme) => theme.id === themeId);
  const chartRows = themes.map((theme) => {
    const row: Record<string, string | number | null> = { tema: theme.nome };
    deputies.forEach((dep) => {
      const candidate = pickTheme(dep.deputado.id, theme.id);
      row[String(dep.deputado.id)] = candidate
        ? (selectedVote === 'sim' ? candidate.percentual_sim : candidate.percentual_nao)
        : null;
    });
    return row;
  });

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Padrão de votos por tema</h2>
          <p className="mt-1 max-w-3xl text-xs leading-relaxed text-slate-500">
            Percentual do voto nominal registrado em votações vinculadas a proposições classificadas por tema.
          </p>
        </div>
        <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
          {(['sim', 'nao'] as const).map((option) => (
            <button type="button" key={option} aria-pressed={selectedVote === option}
              onClick={() => setSelectedVote(option)}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold ${
                selectedVote === option ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
              }`}>
              {option === 'sim' ? 'A favor (Sim)' : 'Contra (Não)'}
            </button>
          ))}
        </div>
      </div>
      <div className="flex flex-wrap gap-4">
        {deputies.map((entry, index) => (
          <span key={entry.deputado.id} className="flex items-center gap-2 text-xs text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: palette[index] }} />
            {entry.deputado.nome_parlamentar}
          </span>
        ))}
      </div>
      {themes.length >= 3 ? (
        <div className="h-[380px] w-full md:h-[440px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartRows} outerRadius="69%" margin={{ top: 22, right: 22, bottom: 22, left: 22 }}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="tema" tick={{ fill: '#475569', fontSize: 11 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tickCount={5} tick={{ fontSize: 10 }} />
              {deputies.map((entry, index) => (
                <Radar key={entry.deputado.id} name={entry.deputado.nome_parlamentar}
                  dataKey={String(entry.deputado.id)} stroke={palette[index]}
                  fill={palette[index]} fillOpacity={0.07}
                  strokeWidth={2} connectNulls={false} />
              ))}
              <Tooltip content={({ active, label }) => {
                if (!active) return null;
                const theme = themes.find((item) => item.nome === label);
                if (!theme) return null;
                return (
                  <div className="max-w-[310px] rounded-xl border border-slate-200 bg-white p-3 text-xs shadow-xl">
                    <strong className="block pb-2 text-slate-800">{theme.nome}</strong>
                    {deputies.map((entry, index) => {
                      const value = pickTheme(entry.deputado.id, theme.id);
                      const pct = selectedVote === 'sim' ? value?.percentual_sim : value?.percentual_nao;
                      return (
                        <p key={entry.deputado.id} className="mb-2 last:mb-0">
                          <span className="font-semibold" style={{ color: palette[index] }}>
                            {entry.deputado.nome_parlamentar}
                          </span>
                          : {prettyPercent(pct)}
                          {value && <span className="block text-slate-500">
                            Sim {value.sim} · Não {value.nao} · Abstenção {value.abstencao} · Obstrução {value.obstrucao}
                          </span>}
                        </p>
                      );
                    })}
                  </div>
                );
              }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-500">
          O radar exige ao menos três temas com registros Sim/Não. Consulte os dados disponíveis abaixo.
        </p>
      )}
      {themes.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-xs">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="py-2 pr-3">Tema</th>
                {deputies.map((entry) => (
                  <th key={entry.deputado.id} className="px-3 py-2">{entry.deputado.nome_parlamentar}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {themes.map((theme) => (
                <tr key={theme.id} className="border-b border-slate-100">
                  <td className="py-3 pr-3 font-semibold text-slate-700">{theme.nome}</td>
                  {deputies.map((entry) => {
                    const item = pickTheme(entry.deputado.id, theme.id);
                    return (
                      <td key={entry.deputado.id} className="px-3 py-3">
                        {prettyPercent(selectedVote === 'sim' ? item?.percentual_sim : item?.percentual_nao)}
                        <span className="block text-[10px] text-slate-400">
                          {item ? `n = ${item.total_sim_nao} (Sim + Não)` : 'Sem registros'}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="border-t border-slate-100 pt-4 text-[11px] leading-relaxed text-slate-500">
        O denominador é Sim + Não por parlamentar e tema. O mesmo voto pode estar ligado a mais
        de um tema. Um voto em emenda, destaque ou requerimento não indica necessariamente
        apoio ou oposição ao mérito de uma política pública; o radar não infere ideologia.
      </p>
    </section>
  );
}

function CommonVotes({ deputies, filters }: {
  deputies: ComparativoDeputado[];
  filters: ComparativoFiltro;
}) {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['comparar-votacoes', filters.ids.join(','), filters.ano, filters.legislatura, page],
    queryFn: () => getComparativoVotacoes({ ...filters, page, page_size: 12 }),
  });
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
      <div className="p-5">
        <h2 className="text-lg font-bold text-slate-900">Votações em comum</h2>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">
          Votações nas quais todos os parlamentares selecionados têm voto registrado. Ausência
          de registro não equivale a voto Não.
        </p>
      </div>
      {isLoading ? <p className="p-5 text-sm text-slate-500">Carregando...</p> :
        isError ? <p className="p-5 text-sm text-rose-700">Não foi possível obter estas votações.</p> :
        !data?.items.length ? <p className="p-5 text-sm text-slate-500">Sem votações em comum registradas neste período.</p> : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[740px] table-fixed text-left">
              <thead className="bg-slate-50 text-xs text-slate-600">
                <tr>
                  <th className="w-[42%] px-5 py-3">Votação</th>
                  {deputies.map((entry) => (
                    <th key={entry.deputado.id} className="px-3 py-3">{entry.deputado.nome_parlamentar}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="border-t border-slate-100 align-top">
                    <td className="px-5 py-4">
                      <p className="text-[11px] text-slate-500">
                        {item.data_hora ? item.data_hora.slice(0, 10).split('-').reverse().join('/') : 'Sem data'}
                        {item.proposicao_nome ? ` · ${item.proposicao_nome}` : ''}
                      </p>
                      <p className="mt-1 line-clamp-3 text-xs font-medium text-slate-800">{item.descricao}</p>
                      <div className="mt-2 flex flex-wrap gap-3 text-[11px] font-semibold text-blue-700">
                        {item.proposicao_id && (
                          <Link to={`/proposicoes/${item.proposicao_id}`} className="hover:underline">
                            Ver proposição
                          </Link>
                        )}
                        {item.uri && (
                          <a href={item.uri} target="_blank" rel="noreferrer"
                            className="inline-flex items-center gap-1 hover:underline">
                            Fonte oficial <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </td>
                    {deputies.map((entry) => (
                      <td key={entry.deputado.id} className="px-3 py-4 text-xs font-semibold text-slate-800">
                        <span className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5">
                          {item.votos[String(entry.deputado.id)] || 'Sem registro'}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
            <span>{data.total} votações · Página {data.page} de {data.total_pages}</span>
            <div className="flex gap-2">
              <button type="button" aria-label="Página anterior" disabled={page === 1}
                onClick={() => setPage((current) => current - 1)}
                className="rounded-lg border border-slate-200 p-2 disabled:opacity-40">
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button type="button" aria-label="Próxima página" disabled={page >= data.total_pages}
                onClick={() => setPage((current) => current + 1)}
                className="rounded-lg border border-slate-200 p-2 disabled:opacity-40">
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

const uniqueIds = (raw: string | null) => (raw || '').split(',').map(Number)
  .filter((id) => Number.isSafeInteger(id) && id > 0)
  .filter((id, index, all) => all.indexOf(id) === index).slice(0, 3);

export function Comparativo() {
  const [params, setParams] = useSearchParams();
  const ids = uniqueIds(params.get('ids'));
  const inputYear = Number(params.get('ano'));
  const year = inputYear >= 2008 && inputYear <= currentYear && Number.isInteger(inputYear)
    ? inputYear : currentYear;
  const inputMonth = Number(params.get('mes'));
  const month = Number.isInteger(inputMonth) && inputMonth >= 1 && inputMonth <= 12
    ? inputMonth : currentMonth;
  const inputLegislature = Number(params.get('legislatura'));
  const legislature = Number.isSafeInteger(inputLegislature) && inputLegislature > 0
    ? inputLegislature : undefined;
  const ready = ids.length >= 2;
  const key = ids.join(',');

  const change = (parts: Record<string, string | undefined>) => {
    const next = new URLSearchParams(params);
    Object.entries(parts).forEach(([field, value]) => {
      if (value) next.set(field, value);
      else next.delete(field);
    });
    setParams(next);
  };

  const { data: profiles } = useQuery({
    queryKey: ['comparar-perfis', key],
    queryFn: () => Promise.all(ids.map((id) => getDeputado(id))),
    enabled: ids.length > 0,
  });
  const { data: legislatures } = useQuery({
    queryKey: ['legislaturas'], queryFn: getLegislaturas,
  });
  const selectedLeg = legislatures?.find((leg) => leg.numero === legislature);
  const fromYear = selectedLeg?.ano_inicio || 2008;
  const toYear = Math.min(selectedLeg?.ano_fim || currentYear, currentYear);
  const yearOptions = Array.from({ length: Math.max(0, toYear - fromYear + 1) },
    (_, i) => toYear - i);
  const { data, isLoading, isError } = useQuery({
    queryKey: ['comparativo', key, year, legislature],
    queryFn: () => getComparativo({ ids, ano: year, legislatura: legislature }),
    enabled: ready,
  });
  const { data: remote, isFetching: loadingRemote } = useQuery({
    queryKey: ['comparativo-indicadores', key, year, month],
    queryFn: () => Promise.all(ids.map(async (id) => {
      try {
        return { id, data: await getDeputadoIndicadores(id, { ano: year, mes: month }) };
      } catch {
        return { id, data: null as DeputadoIndicadores | null };
      }
    })),
    enabled: ready,
    staleTime: 5 * 60 * 1000,
  });
  const indicators: Record<number, DeputadoIndicadores | null> =
    Object.fromEntries((remote || []).map((item) => [item.id, item.data]));
  const selected = ids.map((id) => {
    const present = data?.deputados.find((entry) => entry.deputado.id === id)?.deputado;
    const profile = profiles?.find((entry) => entry.id === id);
    return present || (profile ? {
      id, nome_parlamentar: profile.nome_parlamentar,
      sigla_partido: profile.sigla_partido || null, uf: profile.uf || null,
      url_foto: profile.url_foto || null, dados_demonstrativos: false,
    } satisfies ComparativoParlamentar : undefined);
  });
  const choose = (slot: number, id: number) => {
    if (ids.includes(id)) return;
    const next = [...ids];
    if (slot < next.length) next[slot] = id;
    else if (next.length < 3) next.push(id);
    change({ ids: next.join(',') });
  };

  return (
    <div className="space-y-7">
      <header className="space-y-3">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <GitCompareArrows className="h-4 w-4" /> Comparação factual
        </p>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
          Comparar deputados
        </h1>
        <p className="max-w-4xl text-sm leading-relaxed text-slate-600">
          Escolha dois ou três parlamentares para visualizar indicadores, atividade e votos
          lado a lado, sem notas ou classificações avaliativas.
        </p>
      </header>

      <section className="space-y-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {[0, 1, 2].map((slot) => (
            <Selector key={slot} slot={slot} selected={selected[slot]}
              taken={ids.filter((_, index) => index !== slot)}
              pick={(id) => choose(slot, id)}
              remove={() => change({ ids: ids.filter((_, index) => index !== slot).join(',') })} />
          ))}
        </div>
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex min-w-[150px] flex-col gap-1.5 text-xs font-semibold text-slate-600">
            Legislatura
            <select value={legislature || ''} onChange={(event) => {
              const leg = legislatures?.find((item) => item.numero === Number(event.target.value));
              const nextYear = leg ? Math.max(leg.ano_inicio || 2008,
                Math.min(year, leg.ano_fim || currentYear)) : year;
              change({ legislatura: event.target.value || undefined, ano: String(nextYear) });
            }} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
              <option value="">Todas</option>
              {legislatures?.map((leg) => (
                <option key={leg.numero} value={leg.numero}>
                  {leg.numero}ª ({leg.ano_inicio || '?'}–{leg.ano_fim || '?'})
                </option>
              ))}
            </select>
          </label>
          <label className="flex min-w-[125px] flex-col gap-1.5 text-xs font-semibold text-slate-600">
            Ano
            <select value={year} onChange={(event) => change({ ano: event.target.value })}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
              {yearOptions.map((option) => <option value={option} key={option}>{option}</option>)}
            </select>
          </label>
          <label className="flex min-w-[170px] flex-col gap-1.5 text-xs font-semibold text-slate-600">
            Mês (presença e cota)
            <select value={month} onChange={(event) => change({ mes: event.target.value })}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
              {Array.from({ length: 12 }, (_, index) => (
                <option key={index} value={index + 1}>
                  {new Date(2024, index, 1).toLocaleDateString('pt-BR', { month: 'long' })}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={() => navigator.clipboard?.writeText(window.location.href)}
            className="ml-auto flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100">
            <Share2 className="h-4 w-4" /> Copiar link
          </button>
        </div>
      </section>

      {!ready ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-sm text-slate-500">
          Selecione pelo menos dois deputados distintos para comparar.
        </div>
      ) : isLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">
          Carregando dados da comparação...
        </div>
      ) : isError || !data ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-8 text-sm text-rose-700">
          Não foi possível carregar a comparação. Confira o período e os parlamentares selecionados.
        </div>
      ) : (
        <>
          {data.deputados.some((entry) => entry.deputado.dados_demonstrativos) && (
            <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
              A seleção contém dados demonstrativos. Não interprete esses registros como histórico real.
            </p>
          )}
          <IndicatorSection deputies={data.deputados} indicators={indicators}
            pending={loadingRemote} ano={year} mes={month} />
          <ActivitySection deputies={data.deputados} />
          <VoteSection deputies={data.deputados} />
          <ThemeSection deputies={data.deputados} />
          <CommonVotes key={`${key}-${year}-${legislature || ''}`}
            deputies={data.deputados} filters={{ ids, ano: year, legislatura: legislature }} />
          <div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-600">
            <p className="flex items-center gap-2 font-semibold text-slate-700">
              <Info className="h-4 w-4" /> Notas metodológicas
            </p>
            <p>{data.nota_metodologica}</p>
            <p>
              Presença e cota são consultadas à parte. “—” representa dado indisponível,
              não zero; registros locais podem estar incompletos até a sincronização.
            </p>
            <p>
              Última sincronização registrada: {data.ultima_sincronizacao
                ? data.ultima_sincronizacao.slice(0, 10).split('-').reverse().join('/')
                : 'não informada'}.{' '}
              <Link to="/fontes" className="font-semibold text-blue-700 hover:underline">
                Fontes e datas de acesso
              </Link>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
