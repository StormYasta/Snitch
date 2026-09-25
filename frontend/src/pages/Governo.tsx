import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronRight, Database, ExternalLink, GitBranch, Info,
  Network, Search
} from 'lucide-react';
import { getEstruturaGoverno, searchInstituicoes } from '../api/client';
import type { EstruturaGovernoNode, InstituicaoSimple } from '../types';
import { DetailSkeleton } from '../components/Skeleton';
import { InstitutionGraph } from '../components/InstitutionGraph';

const RELATION_LABELS: Record<string, string> = {
  HIERARQUIA_ADMINISTRATIVA: 'Hierarquia administrativa',
  COMPOSICAO: 'Composição',
  VINCULACAO: 'Vinculação',
  CONTROLE: 'Controle',
  FISCALIZACAO: 'Fiscalização',
};

export function Governo() {
  const navigate = useNavigate();
  const [busca, setBusca] = useState('');
  const [selectedId, setSelectedId] = useState<number>();
  const [focusId, setFocusId] = useState<number>();
  const [focusToken, setFocusToken] = useState(0);

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
    data?.nodes.forEach((node) => map.set(node.id, node));
    return map;
  }, [data]);

  const childrenByParent = useMemo(() => {
    const map = new Map<number, EstruturaGovernoNode[]>();
    data?.nodes.forEach((node) => {
      if (!node.parentId) return;
      const children = map.get(node.parentId) || [];
      children.push(node);
      map.set(node.parentId, children);
    });
    map.forEach((children) => children.sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')));
    return map;
  }, [data]);

  useEffect(() => {
    if (!data || selectedId !== undefined) return;
    const uniao = data.nodes.find((node) => node.codigo_externo === 'UNIAO');
    const initial = uniao || data.nodes.find((node) => !node.parentId) || data.nodes[0];
    if (initial) {
      setSelectedId(initial.id);
      setFocusId(initial.id);
      setFocusToken((value) => value + 1);
    }
  }, [data, selectedId]);

  const selectedNode = selectedId !== undefined ? nodeById.get(selectedId) : undefined;

  const parentNode = useMemo(() => {
    if (!selectedNode?.parentId) return undefined;
    return nodeById.get(selectedNode.parentId);
  }, [nodeById, selectedNode]);

  const selectedChildren = useMemo(() => {
    if (!selectedNode) return [];
    return childrenByParent.get(selectedNode.id) || [];
  }, [childrenByParent, selectedNode]);

  const selectedRelations = useMemo(() => {
    if (!data || !selectedNode) return [];
    return data.edges.filter(
      (edge) => edge.source === selectedNode.id || edge.target === selectedNode.id
    );
  }, [data, selectedNode]);

  const breadcrumb = useMemo(() => {
    if (!selectedNode) return [];
    const chain: EstruturaGovernoNode[] = [selectedNode];
    const visited = new Set<number>([selectedNode.id]);
    let cursor = selectedNode;

    while (cursor.parentId && !visited.has(cursor.parentId)) {
      const parent = nodeById.get(cursor.parentId);
      if (!parent) break;
      chain.unshift(parent);
      visited.add(parent.id);
      cursor = parent;
    }
    return chain;
  }, [nodeById, selectedNode]);

  const federativeRoots = useMemo(() => {
    if (!data) return [];
    const wanted = ['UNIAO', 'ESTADOS', 'DF', 'MUNICIPIOS'];
    return wanted
      .map((code) => data.nodes.find((node) => node.codigo_externo === code))
      .filter((node): node is EstruturaGovernoNode => Boolean(node));
  }, [data]);

  const focusNode = (node: EstruturaGovernoNode) => {
    setSelectedId(node.id);
    setFocusId(node.id);
    setFocusToken((value) => value + 1);
  };

  const chooseSearchResult = (item: InstituicaoSimple) => {
    const graphNode = nodeById.get(item.id);
    setBusca('');
    if (graphNode) {
      focusNode(graphNode);
      return;
    }
    navigate(`/governo/instituicoes/${item.id}`);
  };

  if (isLoading) return <DetailSkeleton />;

  if (isError || !data) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-10 text-rose-700">
        Não foi possível carregar o mapa institucional.
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <section className="space-y-3">
        <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <Network className="h-4 w-4" />
          Mapa institucional
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 md:text-4xl">
          Entenda o Governo
        </h1>
        <p className="max-w-4xl text-sm leading-relaxed text-slate-600 md:text-base">
          Navegue visualmente pela estrutura institucional. Expanda os nós, arraste o mapa,
          use o zoom e selecione uma instituição para entender suas relações.
        </p>
      </section>

      <section className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="relative w-full max-w-2xl">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <input
            value={busca}
            onChange={(event) => setBusca(event.target.value)}
            placeholder="Buscar órgão ou instituição..."
            className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm shadow-xs focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          {busca.trim().length >= 2 && (
            <div className="absolute left-0 right-0 z-30 mt-2 max-h-80 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl">
              {resultados?.length ? resultados.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => chooseSearchResult(item)}
                  className="flex w-full items-center justify-between gap-3 border-b border-slate-100 px-4 py-3 text-left last:border-b-0 hover:bg-slate-50"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-slate-900">{item.nome}</div>
                    <div className="mt-0.5 text-xs text-slate-500">
                      {item.sigla ? `${item.sigla} • ` : ''}{item.tipo.replaceAll('_', ' ')}
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />
                </button>
              )) : (
                <div className="px-4 py-3 text-sm text-slate-500">
                  Nenhuma instituição encontrada.
                </div>
              )}
            </div>
          )}
        </div>

        {federativeRoots.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {federativeRoots.map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => focusNode(node)}
                className={[
                  'rounded-lg border px-3 py-2 text-xs font-semibold transition-colors',
                  selectedId === node.id
                    ? 'border-slate-900 bg-slate-900 text-white'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50',
                ].join(' ')}
              >
                {node.nome}
              </button>
            ))}
          </div>
        )}
      </section>

      {breadcrumb.length > 0 && (
        <nav className="flex flex-wrap items-center gap-1.5 text-xs text-slate-500" aria-label="Caminho institucional">
          {breadcrumb.map((node, index) => (
            <span key={node.id} className="inline-flex items-center gap-1.5">
              {index > 0 && <ChevronRight className="h-3 w-3 text-slate-300" />}
              <button
                type="button"
                onClick={() => focusNode(node)}
                className={index === breadcrumb.length - 1 ? 'font-semibold text-slate-900' : 'hover:text-slate-800'}
              >
                {node.sigla || node.nome}
              </button>
            </span>
          ))}
        </nav>
      )}

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">
        <div className="h-[660px] min-w-0">
          <InstitutionGraph
            graph={data}
            selectedId={selectedId}
            focusId={focusId}
            focusToken={focusToken}
            onSelect={(node) => setSelectedId(node.id)}
          />
        </div>

        <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs xl:h-[660px] xl:overflow-y-auto">
          {selectedNode ? (
            <div className="space-y-5">
              <div>
                <div className="mb-2 flex flex-wrap gap-2">
                  {selectedNode.sigla && (
                    <span className="rounded bg-slate-900 px-2 py-0.5 text-[10px] font-bold text-white">
                      {selectedNode.sigla}
                    </span>
                  )}
                  <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                    {selectedNode.tipo.replaceAll('_', ' ')}
                  </span>
                </div>
                <h2 className="text-xl font-extrabold leading-tight text-slate-900">
                  {selectedNode.nome}
                </h2>
                <p className="mt-2 text-xs text-slate-500">
                  {selectedNode.poder} • {selectedNode.esfera} • {selectedNode.nivel_federativo}
                </p>
              </div>

              {selectedNode.descricao && (
                <p className="border-t border-slate-100 pt-4 text-xs leading-relaxed text-slate-600">
                  {selectedNode.descricao}
                </p>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-slate-50 p-3">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Unidades abaixo
                  </div>
                  <div className="mt-1 text-xl font-extrabold text-slate-900">{selectedChildren.length}</div>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Relações no mapa
                  </div>
                  <div className="mt-1 text-xl font-extrabold text-slate-900">{selectedRelations.length}</div>
                </div>
              </div>

              {parentNode && (
                <div>
                  <div className="mb-2 flex items-center gap-2 text-xs font-bold text-slate-700">
                    <GitBranch className="h-4 w-4" />
                    Estrutura superior
                  </div>
                  <button
                    type="button"
                    onClick={() => focusNode(parentNode)}
                    className="flex w-full items-center justify-between rounded-xl bg-slate-50 px-3 py-3 text-left hover:bg-slate-100"
                  >
                    <span className="min-w-0 truncate text-xs font-semibold text-slate-800">
                      {parentNode.sigla || parentNode.nome}
                    </span>
                    <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                  </button>
                </div>
              )}

              {selectedChildren.length > 0 && (
                <div>
                  <div className="mb-2 text-xs font-bold text-slate-700">Unidades diretamente relacionadas</div>
                  <div className="space-y-1.5">
                    {selectedChildren.slice(0, 8).map((child) => (
                      <button
                        key={child.id}
                        type="button"
                        onClick={() => focusNode(child)}
                        className="flex w-full items-center justify-between rounded-lg border border-slate-100 px-3 py-2 text-left hover:bg-slate-50"
                      >
                        <span className="min-w-0 truncate text-xs text-slate-700">
                          {child.sigla || child.nome}
                        </span>
                        <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-300" />
                      </button>
                    ))}
                    {selectedChildren.length > 8 && (
                      <div className="px-1 pt-1 text-[10px] text-slate-400">
                        + {selectedChildren.length - 8} outras unidades no diagrama
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedRelations.length > 0 && (
                <div>
                  <div className="mb-2 text-xs font-bold text-slate-700">Tipos de relação</div>
                  <div className="flex flex-wrap gap-1.5">
                    {Array.from(new Set(selectedRelations.map((edge) => edge.tipo_relacao))).map((relation) => (
                      <span
                        key={relation}
                        className="rounded-md border border-slate-200 bg-white px-2 py-1 text-[10px] text-slate-500"
                      >
                        {RELATION_LABELS[relation] || relation.replaceAll('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="space-y-2 border-t border-slate-100 pt-4">
                <Link
                  to={`/governo/instituicoes/${selectedNode.id}`}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-800"
                >
                  Abrir detalhes completos
                  <ChevronRight className="h-3.5 w-3.5" />
                </Link>
                {selectedNode.site_oficial && (
                  <a
                    href={selectedNode.site_oficial}
                    target="_blank"
                    rel="noreferrer"
                    className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Site institucional
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
            </div>
          ) : (
            <div className="flex h-full min-h-60 items-center justify-center text-center text-sm text-slate-400">
              Selecione um nó do diagrama.
            </div>
          )}
        </aside>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <Info className="h-5 w-5 shrink-0 text-slate-500" />
          <p className="text-xs leading-relaxed text-slate-600">
            O diagrama diferencia relações estruturais de vinculação, controle e fiscalização.
            Relações não estruturais aparecem quando uma instituição envolvida é selecionada.
          </p>
        </div>
        <div className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <Database className="h-5 w-5 shrink-0 text-slate-500" />
          <p className="text-xs leading-relaxed text-slate-600">
            A visualização usa o grafo institucional já armazenado no Snitch e mantém acesso
            à página detalhada de cada instituição.
          </p>
        </div>
      </section>
    </div>
  );
}
