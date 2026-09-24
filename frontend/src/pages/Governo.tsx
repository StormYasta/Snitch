import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Building2, Search, Landmark, Scale, Gavel, Network,
  ChevronRight, Database, Info
} from 'lucide-react';
import { getEstruturaGoverno, searchInstituicoes } from '../api/client';
import type { EstruturaGovernoNode } from '../types';
import { DetailSkeleton } from '../components/Skeleton';

const powerIcon = (poder: string) => {
  if (poder === 'Legislativo') return <Landmark className="w-5 h-5" />;
  if (poder === 'Judiciário') return <Gavel className="w-5 h-5" />;
  if (poder === 'Executivo') return <Building2 className="w-5 h-5" />;
  return <Scale className="w-5 h-5" />;
};

export const Governo: React.FC = () => {
  const [busca, setBusca] = useState('');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['estrutura-governo'],
    queryFn: getEstruturaGoverno,
  });

  const { data: resultados } = useQuery({
    queryKey: ['governo-busca', busca],
    queryFn: () => searchInstituicoes(busca),
    enabled: busca.trim().length >= 2,
  });

  const nodeById = useMemo(() => {
    const map = new Map<number, EstruturaGovernoNode>();
    data?.nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [data]);

  const byCode = (code: string) => data?.nodes.find((n) => n.codigo_externo === code);
  const childrenOf = (parentId?: number) => {
    if (!parentId || !data) return [];
    return data.edges
      .filter((e) => e.target === parentId && ['COMPOSICAO', 'HIERARQUIA_ADMINISTRATIVA'].includes(e.tipo_relacao))
      .map((e) => nodeById.get(e.source))
      .filter(Boolean) as EstruturaGovernoNode[];
  };

  if (isLoading) return <DetailSkeleton />;

  if (isError || !data) {
    return (
      <div className="p-10 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700">
        Não foi possível carregar o mapa institucional.
      </div>
    );
  }

  const federativos = ['UNIAO', 'ESTADOS', 'DF', 'MUNICIPIOS']
    .map(byCode)
    .filter(Boolean) as EstruturaGovernoNode[];

  const uniao = byCode('UNIAO');
  const poderesUniao = childrenOf(uniao?.id).filter((n) =>
    ['PODER', 'GRUPO_INSTITUCIONAL'].includes(n.tipo)
  );

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <Network className="w-4 h-4" />
          Estrutura institucional
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900">
          Entenda o Governo
        </h1>
        <p className="text-sm md:text-base text-slate-600 max-w-4xl leading-relaxed">
          Explore como os entes federativos, Poderes, órgãos e instituições públicas se organizam.
          As conexões representam composição, hierarquia administrativa, vinculação ou controle —
          não uma cadeia única de comando.
        </p>
      </section>

      <section className="relative max-w-2xl">
        <div className="relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
          <input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar Congresso, Câmara, STF, Ministério da Saúde..."
            className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-4 py-2.5 text-sm shadow-xs focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        {busca.trim().length >= 2 && (
          <div className="absolute z-20 left-0 right-0 mt-2 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden">
            {resultados?.length ? resultados.map((item) => (
              <Link
                key={item.id}
                to={`/governo/instituicoes/${item.id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-50 border-b last:border-b-0 border-slate-100"
              >
                <div>
                  <div className="text-sm font-semibold text-slate-900">{item.nome}</div>
                  <div className="text-xs text-slate-500">
                    {item.sigla ? `${item.sigla} • ` : ''}{item.tipo} • {item.esfera}
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
            )) : (
              <div className="px-4 py-3 text-sm text-slate-500">Nenhuma instituição encontrada.</div>
            )}
          </div>
        )}
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Organização federativa</h2>
          <p className="text-xs text-slate-500 mt-1">
            União, estados, Distrito Federal e municípios possuem competências próprias.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {federativos.map((node) => (
            <Link
              key={node.id}
              to={`/governo/instituicoes/${node.id}`}
              className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-xs hover:shadow-md hover:border-slate-300 transition-all"
            >
              <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700 mb-4">
                <Landmark className="w-5 h-5" />
              </div>
              <div className="font-bold text-slate-900 group-hover:text-blue-600">{node.nome}</div>
              <div className="text-xs text-slate-500 mt-1">{node.nivel_federativo}</div>
              <div className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-slate-600">
                Explorar <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {uniao && (
        <section className="space-y-5">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">União</h2>
              <p className="text-sm text-slate-500">
                Os Poderes são apresentados lado a lado. Relações administrativas internas aparecem dentro de cada área.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {poderesUniao.map((poder) => {
              const children = childrenOf(poder.id).slice(0, 12);
              return (
                <div key={poder.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                  <Link to={`/governo/instituicoes/${poder.id}`} className="group flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
                        {powerIcon(poder.poder)}
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-900 group-hover:text-blue-600">{poder.nome}</h3>
                        <p className="text-xs text-slate-500 mt-1">{poder.natureza_juridica || poder.tipo}</p>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400 mt-1" />
                  </Link>

                  {children.length > 0 && (
                    <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {children.map((child) => (
                        <Link
                          key={child.id}
                          to={`/governo/instituicoes/${child.id}`}
                          className="rounded-lg bg-slate-50 hover:bg-slate-100 px-3 py-2 text-xs text-slate-700 transition-colors"
                        >
                          <span className="font-semibold">{child.sigla || child.nome}</span>
                          {child.sigla && <span className="block text-slate-500 mt-0.5 truncate">{child.nome}</span>}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 flex gap-3">
          <Info className="w-5 h-5 text-slate-500 shrink-0" />
          <p className="text-xs text-slate-600 leading-relaxed">
            O mapa evita representar relações de controle, composição ou revisão como se fossem
            subordinação administrativa. Abra uma instituição para ver o tipo de cada relação.
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 flex gap-3">
          <Database className="w-5 h-5 text-slate-500 shrink-0" />
          <p className="text-xs text-slate-600 leading-relaxed">
            Estrutura do Executivo Federal: SIORG. Estrutura constitucional de alto nível:
            fontes institucionais oficiais. A Câmara está conectada ao módulo legislativo do Snitch.
          </p>
        </div>
      </section>
    </div>
  );
};
