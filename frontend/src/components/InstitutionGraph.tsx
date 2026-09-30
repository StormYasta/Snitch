import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ChevronDown, ChevronRight, Maximize2, Minus, Plus, RotateCcw
} from 'lucide-react';
import type {
  EstruturaGovernoEdge,
  EstruturaGovernoGraph,
  EstruturaGovernoNode
} from '../types';

const NODE_WIDTH = 236;
const NODE_HEIGHT = 92;
const LEVEL_GAP = 116;
const ROW_GAP = 30;
const CANVAS_PADDING = 64;
const STRUCTURAL_RELATIONS = new Set(['HIERARQUIA_ADMINISTRATIVA', 'COMPOSICAO']);

type ViewTransform = {
  x: number;
  y: number;
  scale: number;
};

type PositionedNode = {
  node: EstruturaGovernoNode;
  x: number;
  y: number;
  depth: number;
};

interface InstitutionGraphProps {
  graph: EstruturaGovernoGraph;
  selectedId?: number;
  focusId?: number;
  focusToken?: number;
  onSelect: (node: EstruturaGovernoNode) => void;
}

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

const rootPriority = (node: EstruturaGovernoNode) => {
  const priorities: Record<string, number> = {
    UNIAO: 0,
    ESTADOS: 1,
    DF: 2,
    MUNICIPIOS: 3,
  };
  return priorities[node.codigo_externo || ''] ?? 20;
};

const nodeTone = (node: EstruturaGovernoNode) => {
  if (node.codigo_externo === 'UNIAO') return 'border-slate-900 bg-slate-900 text-white';
  if (node.tipo === 'PODER') return 'border-blue-200 bg-blue-50 text-blue-950';
  if (node.tipo === 'MINISTERIO') return 'border-indigo-200 bg-indigo-50 text-indigo-950';
  if (node.tipo === 'CASA_LEGISLATIVA') return 'border-violet-200 bg-violet-50 text-violet-950';
  if (node.tipo === 'TRIBUNAL') return 'border-amber-200 bg-amber-50 text-amber-950';
  if (node.tipo === 'AUTARQUIA' || node.tipo === 'FUNDACAO') return 'border-emerald-200 bg-emerald-50 text-emerald-950';
  return 'border-slate-200 bg-white text-slate-900';
};

const edgeStyle = (edge: EstruturaGovernoEdge) => {
  if (edge.tipo_relacao === 'VINCULACAO') {
    return { className: 'stroke-blue-400', dash: '8 6' };
  }
  if (edge.tipo_relacao === 'CONTROLE' || edge.tipo_relacao === 'FISCALIZACAO') {
    return { className: 'stroke-amber-400', dash: '3 6' };
  }
  return { className: 'stroke-slate-300', dash: undefined };
};

export function InstitutionGraph({
  graph,
  selectedId,
  focusId,
  focusToken = 0,
  onSelect,
}: InstitutionGraphProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);
  const didFitRef = useRef(false);

  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [transform, setTransform] = useState<ViewTransform>({ x: 24, y: 24, scale: 0.86 });
  const [pendingCenter, setPendingCenter] = useState<number | null>(null);

  const nodeById = useMemo(() => {
    const map = new Map<number, EstruturaGovernoNode>();
    graph.nodes.forEach((node) => map.set(node.id, node));
    return map;
  }, [graph.nodes]);

  const parentByChild = useMemo(() => {
    const map = new Map<number, number>();
    graph.nodes.forEach((node) => {
      if (node.parentId && nodeById.has(node.parentId)) {
        map.set(node.id, node.parentId);
      }
    });
    graph.edges.forEach((edge) => {
      if (
        STRUCTURAL_RELATIONS.has(edge.tipo_relacao) &&
        nodeById.has(edge.source) &&
        nodeById.has(edge.target) &&
        !map.has(edge.source)
      ) {
        map.set(edge.source, edge.target);
      }
    });
    return map;
  }, [graph.edges, graph.nodes, nodeById]);

  const childrenByParent = useMemo(() => {
    const map = new Map<number, EstruturaGovernoNode[]>();
    parentByChild.forEach((parentId, childId) => {
      const child = nodeById.get(childId);
      if (!child) return;
      const children = map.get(parentId) || [];
      children.push(child);
      map.set(parentId, children);
    });
    map.forEach((children) => children.sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')));
    return map;
  }, [nodeById, parentByChild]);

  const roots = useMemo(() => {
    return graph.nodes
      .filter((node) => !parentByChild.has(node.id))
      .sort((a, b) => {
        const priorityDiff = rootPriority(a) - rootPriority(b);
        return priorityDiff !== 0 ? priorityDiff : a.nome.localeCompare(b.nome, 'pt-BR');
      });
  }, [graph.nodes, parentByChild]);

  const buildInitialExpanded = useCallback(() => {
    const next = new Set<number>();
    const uniao = graph.nodes.find((node) => node.codigo_externo === 'UNIAO') || roots[0];
    if (uniao) {
      next.add(uniao.id);
      (childrenByParent.get(uniao.id) || []).forEach((child) => next.add(child.id));
    }
    return next;
  }, [childrenByParent, graph.nodes, roots]);

  useEffect(() => {
    setExpanded(buildInitialExpanded());
    didFitRef.current = false;
  }, [buildInitialExpanded]);

  const layout = useMemo(() => {
    const levels = new Map<number, EstruturaGovernoNode[]>();
    const visibleIds = new Set<number>();

    const visit = (node: EstruturaGovernoNode, depth: number) => {
      if (visibleIds.has(node.id)) return;
      visibleIds.add(node.id);
      const level = levels.get(depth) || [];
      level.push(node);
      levels.set(depth, level);

      if (!expanded.has(node.id)) return;
      (childrenByParent.get(node.id) || []).forEach((child) => visit(child, depth + 1));
    };

    roots.forEach((root) => visit(root, 0));

    const positions = new Map<number, PositionedNode>();
    let maxRows = 1;
    let maxDepth = 0;

    levels.forEach((nodes, depth) => {
      maxRows = Math.max(maxRows, nodes.length);
      maxDepth = Math.max(maxDepth, depth);
      nodes.forEach((node, index) => {
        positions.set(node.id, {
          node,
          depth,
          x: CANVAS_PADDING + depth * (NODE_WIDTH + LEVEL_GAP),
          y: CANVAS_PADDING + index * (NODE_HEIGHT + ROW_GAP),
        });
      });
    });

    return {
      positions,
      visibleIds,
      width: CANVAS_PADDING * 2 + (maxDepth + 1) * NODE_WIDTH + maxDepth * LEVEL_GAP,
      height: CANVAS_PADDING * 2 + maxRows * NODE_HEIGHT + Math.max(0, maxRows - 1) * ROW_GAP,
    };
  }, [childrenByParent, expanded, roots]);

  const fitView = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const width = Math.max(layout.width, 1);
    const height = Math.max(layout.height, 1);
    const scale = clamp(
      Math.min((viewport.clientWidth - 48) / width, (viewport.clientHeight - 48) / height),
      0.34,
      1.08,
    );

    setTransform({
      scale,
      x: (viewport.clientWidth - width * scale) / 2,
      y: (viewport.clientHeight - height * scale) / 2,
    });
  }, [layout.height, layout.width]);

  useEffect(() => {
    if (didFitRef.current || layout.positions.size === 0) return;
    const frame = window.requestAnimationFrame(() => {
      fitView();
      didFitRef.current = true;
    });
    return () => window.cancelAnimationFrame(frame);
  }, [fitView, layout.positions.size]);

  const revealNode = useCallback((nodeId: number) => {
    if (!nodeById.has(nodeId)) return;

    setExpanded((current) => {
      const next = new Set(current);
      let cursor: number | undefined = nodeId;
      let guard = 0;

      while (cursor !== undefined && guard < graph.nodes.length + 1) {
        const parent = parentByChild.get(cursor);
        if (parent === undefined) break;
        next.add(parent);
        cursor = parent;
        guard += 1;
      }
      return next;
    });
    setPendingCenter(nodeId);
  }, [graph.nodes.length, nodeById, parentByChild]);

  useEffect(() => {
    if (focusId === undefined) return;
    revealNode(focusId);
  }, [focusId, focusToken, revealNode]);

  useEffect(() => {
    if (pendingCenter === null) return;
    const positioned = layout.positions.get(pendingCenter);
    const viewport = viewportRef.current;
    if (!positioned || !viewport) return;

    setTransform((current) => {
      const scale = Math.max(current.scale, 0.72);
      const centerX = positioned.x + NODE_WIDTH / 2;
      const centerY = positioned.y + NODE_HEIGHT / 2;
      return {
        scale,
        x: viewport.clientWidth / 2 - centerX * scale,
        y: viewport.clientHeight / 2 - centerY * scale,
      };
    });
    setPendingCenter(null);
  }, [layout.positions, pendingCenter]);

  const toggleNode = (nodeId: number) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const zoomAtCenter = (delta: number) => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    setTransform((current) => {
      const nextScale = clamp(current.scale + delta, 0.28, 1.8);
      const centerX = viewport.clientWidth / 2;
      const centerY = viewport.clientHeight / 2;
      const worldX = (centerX - current.x) / current.scale;
      const worldY = (centerY - current.y) / current.scale;

      return {
        scale: nextScale,
        x: centerX - worldX * nextScale,
        y: centerY - worldY * nextScale,
      };
    });
  };

  const handleWheel = (event: React.WheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    const viewport = viewportRef.current;
    if (!viewport) return;

    const rect = viewport.getBoundingClientRect();
    const pointerX = event.clientX - rect.left;
    const pointerY = event.clientY - rect.top;

    setTransform((current) => {
      const nextScale = clamp(current.scale * (event.deltaY > 0 ? 0.9 : 1.1), 0.28, 1.8);
      const worldX = (pointerX - current.x) / current.scale;
      const worldY = (pointerY - current.y) / current.scale;

      return {
        scale: nextScale,
        x: pointerX - worldX * nextScale,
        y: pointerY - worldY * nextScale,
      };
    });
  };

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      originX: transform.x,
      originY: transform.y,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    setTransform((current) => ({
      ...current,
      x: drag.originX + event.clientX - drag.startX,
      y: drag.originY + event.clientY - drag.startY,
    }));
  };

  const stopDragging = (event: React.PointerEvent<HTMLDivElement>) => {
    if (dragRef.current?.pointerId === event.pointerId) {
      dragRef.current = null;
      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
    }
  };

  const resetView = () => {
    setExpanded(buildInitialExpanded());
    window.requestAnimationFrame(() => fitView());
  };

  const visibleEdges = graph.edges.filter((edge) => {
    if (!layout.visibleIds.has(edge.source) || !layout.visibleIds.has(edge.target)) return false;
    if (STRUCTURAL_RELATIONS.has(edge.tipo_relacao)) return true;
    return selectedId === edge.source || selectedId === edge.target;
  });

  return (
    <div className="relative h-full min-h-[560px] overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
      <div className="absolute left-4 top-4 z-20 rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-[11px] text-slate-500 shadow-sm backdrop-blur">
        Arraste para mover • use a roda para aproximar
      </div>

      <div className="absolute right-4 top-4 z-20 flex overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <button
          type="button"
          onClick={() => zoomAtCenter(0.14)}
          className="p-2 text-slate-600 hover:bg-slate-50"
          aria-label="Aumentar zoom"
        >
          <Plus className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => zoomAtCenter(-0.14)}
          className="border-l border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
          aria-label="Diminuir zoom"
        >
          <Minus className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={fitView}
          className="border-l border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
          aria-label="Ajustar diagrama à tela"
        >
          <Maximize2 className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={resetView}
          className="border-l border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
          aria-label="Redefinir diagrama"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      <div
        ref={viewportRef}
        className="absolute inset-0 cursor-grab active:cursor-grabbing"
        style={{
          touchAction: 'none',
          backgroundImage: 'radial-gradient(circle, rgb(203 213 225 / 0.75) 1px, transparent 1px)',
          backgroundSize: '22px 22px',
        }}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={stopDragging}
        onPointerCancel={stopDragging}
      >
        <div
          className="absolute left-0 top-0"
          style={{
            width: layout.width,
            height: layout.height,
            transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
            transformOrigin: '0 0',
          }}
        >
          <svg
            className="pointer-events-none absolute inset-0 overflow-visible"
            width={layout.width}
            height={layout.height}
            aria-hidden="true"
          >
            {visibleEdges.map((edge) => {
              const source = layout.positions.get(edge.source);
              const target = layout.positions.get(edge.target);
              if (!source || !target) return null;

              const structural = STRUCTURAL_RELATIONS.has(edge.tipo_relacao);
              const from = structural ? target : source;
              const to = structural ? source : target;

              const x1 = from.x + NODE_WIDTH;
              const y1 = from.y + NODE_HEIGHT / 2;
              const x2 = to.x;
              const y2 = to.y + NODE_HEIGHT / 2;
              const curve = Math.max(52, Math.abs(x2 - x1) * 0.46);
              const path = `M ${x1} ${y1} C ${x1 + curve} ${y1}, ${x2 - curve} ${y2}, ${x2} ${y2}`;
              const style = edgeStyle(edge);
              const active = selectedId === edge.source || selectedId === edge.target;

              return (
                <path
                  key={edge.id}
                  d={path}
                  fill="none"
                  className={style.className}
                  strokeWidth={active ? 2.6 : 1.6}
                  strokeDasharray={style.dash}
                  opacity={active ? 1 : 0.78}
                />
              );
            })}
          </svg>

          {Array.from(layout.positions.values()).map(({ node, x, y }) => {
            const children = childrenByParent.get(node.id) || [];
            const isExpanded = expanded.has(node.id);
            const isSelected = selectedId === node.id;

            return (
              <div
                key={node.id}
                className="absolute"
                style={{ left: x, top: y, width: NODE_WIDTH, height: NODE_HEIGHT }}
                onPointerDown={(event) => event.stopPropagation()}
              >
                <div
                  className={[
                    'relative h-full rounded-xl border shadow-sm transition-all',
                    nodeTone(node),
                    isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : 'hover:shadow-md',
                  ].join(' ')}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(node)}
                    onDoubleClick={() => children.length > 0 && toggleNode(node.id)}
                    className="flex h-full w-full flex-col items-start px-4 py-3 text-left"
                  >
                    <div className="mb-1 flex w-full items-center justify-between gap-2">
                      <span className="truncate text-[10px] font-bold uppercase tracking-wider opacity-60">
                        {node.tipo.replaceAll('_', ' ')}
                      </span>
                      {node.integrado && (
                        <span className="rounded bg-blue-600 px-1.5 py-0.5 text-[9px] font-bold text-white">
                          integrado
                        </span>
                      )}
                    </div>
                    <div className="line-clamp-2 text-sm font-bold leading-snug">
                      {node.sigla || node.nome}
                    </div>
                    {node.sigla && (
                      <div className="mt-1 max-w-full truncate text-[10px] opacity-65">
                        {node.nome}
                      </div>
                    )}
                  </button>

                  {children.length > 0 && (
                    <button
                      type="button"
                      onClick={() => toggleNode(node.id)}
                      className="absolute -right-3 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50"
                      aria-label={isExpanded ? 'Recolher unidades' : 'Expandir unidades'}
                      title={isExpanded ? 'Recolher unidades' : `Expandir ${children.length} unidades`}
                    >
                      {isExpanded
                        ? <ChevronDown className="h-3.5 w-3.5" />
                        : <ChevronRight className="h-3.5 w-3.5" />}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="absolute bottom-4 left-4 z-20 flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-[10px] text-slate-500 shadow-sm backdrop-blur">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-px w-6 bg-slate-400" />
          Estrutura
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-6 border-t border-dashed border-blue-400" />
          Vinculação
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-6 border-t border-dotted border-amber-400" />
          Controle / fiscalização
        </span>
      </div>
    </div>
  );
}
