import { useMemo, useState } from 'react';
import { CalendarDays, Database, ExternalLink, Search, ShieldCheck } from 'lucide-react';
import { officialSources, SOURCES_LAST_REVIEW } from '../data/sources';

const categoryOrder = [
  'Dados legislativos',
  'Presença parlamentar',
  'Estrutura organizacional',
  'Base constitucional',
  'Referência institucional',
];

export function Fontes() {
  const [query, setQuery] = useState('');

  const filteredSources = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase('pt-BR');
    if (!normalized) return officialSources;

    return officialSources.filter((source) =>
      [
        source.name,
        source.organization,
        source.category,
        source.usage,
        source.url,
        source.endpoint || '',
      ]
        .join(' ')
        .toLocaleLowerCase('pt-BR')
        .includes(normalized)
    );
  }, [query]);

  const grouped = useMemo(() => {
    return categoryOrder
      .map((category) => ({
        category,
        items: filteredSources.filter((source) => source.category === category),
      }))
      .filter((group) => group.items.length > 0);
  }, [filteredSources]);

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs md:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-3 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <ShieldCheck className="h-4 w-4" />
              Rastreabilidade
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 md:text-4xl">
              Fontes dos dados
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-600">
              Esta página reúne as fontes externas utilizadas pelo Snitch para dados legislativos,
              presença parlamentar e estrutura institucional. Cada registro informa onde a fonte é
              utilizada e a data em que o endereço foi acessado e conferido.
            </p>
          </div>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            <div className="flex items-center gap-2 font-semibold">
              <CalendarDays className="h-4 w-4" />
              Última revisão das fontes
            </div>
            <div className="mt-1 text-xs text-emerald-700">{SOURCES_LAST_REVIEW}</div>
          </div>
        </div>
      </section>

      <section className="relative max-w-2xl">
        <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar Câmara, SIORG, STF, Constituição..."
          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm shadow-xs focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Fontes catalogadas</div>
          <div className="mt-1 text-2xl font-extrabold text-slate-900">{officialSources.length}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Fontes primárias de dados</div>
          <div className="mt-1 text-2xl font-extrabold text-slate-900">
            {officialSources.filter((source) => source.category !== 'Referência institucional').length}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Revisão</div>
          <div className="mt-1 text-lg font-extrabold text-slate-900">{SOURCES_LAST_REVIEW}</div>
        </div>
      </section>

      <div className="space-y-8">
        {grouped.map((group) => (
          <section key={group.category} className="space-y-3">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-slate-500" />
              <h2 className="text-lg font-bold text-slate-900">{group.category}</h2>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                {group.items.length}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {group.items.map((source) => (
                <article
                  key={source.url}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-slate-500">{source.organization}</div>
                      <h3 className="mt-1 text-base font-bold text-slate-900">{source.name}</h3>
                      <p className="mt-2 max-w-4xl text-xs leading-relaxed text-slate-600">
                        {source.usage}
                      </p>

                      {source.endpoint && (
                        <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2 font-mono text-[11px] text-slate-500 break-all">
                          Endpoint: {source.endpoint}
                        </div>
                      )}
                    </div>

                    <div className="flex shrink-0 flex-col items-start gap-2 lg:items-end">
                      <div className="inline-flex items-center gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-[11px] text-slate-500">
                        <CalendarDays className="h-3.5 w-3.5" />
                        Acesso: <strong className="font-semibold text-slate-700">{source.accessedAt}</strong>
                      </div>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Abrir fonte
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>

      {filteredSources.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
          Nenhuma fonte corresponde à busca.
        </div>
      )}

      <section className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs leading-relaxed text-slate-600">
        <strong className="text-slate-800">Sobre a data de acesso:</strong>{' '}
        ela registra quando o endereço da fonte foi conferido para esta versão do projeto. Não é a data
        de publicação do conteúdo nem, necessariamente, a data da última atualização realizada pelo órgão.
        As páginas individuais de instituições continuam exibindo seus próprios links oficiais quando disponíveis.
      </section>
    </div>
  );
}
