import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, Building2, ExternalLink, GitBranch, Link2,
  Database, Users, FileText, Vote, Landmark
} from 'lucide-react';
import { getInstituicao } from '../api/client';
import type { InstituicaoSimple } from '../types';
import { DetailSkeleton } from '../components/Skeleton';

const RelationList: React.FC<{
  title: string;
  items: InstituicaoSimple[];
  icon: React.ReactNode;
  empty?: string;
}> = ({ title, items, icon, empty = 'Nenhum registro nesta categoria.' }) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
    <div className="flex items-center gap-2 mb-4">
      {icon}
      <h2 className="font-bold text-slate-900">{title}</h2>
    </div>
    {items.length === 0 ? (
      <p className="text-xs text-slate-400">{empty}</p>
    ) : (
      <div className="space-y-2">
        {items.map((item) => (
          <Link
            key={item.id}
            to={`/governo/instituicoes/${item.id}`}
            className="flex items-center justify-between rounded-xl bg-slate-50 hover:bg-slate-100 px-3 py-3 transition-colors"
          >
            <div className="min-w-0">
              <div className="text-sm font-semibold text-slate-800 truncate">{item.nome}</div>
              <div className="text-[11px] text-slate-500">
                {item.sigla ? `${item.sigla} • ` : ''}{item.tipo}
              </div>
            </div>
            <span className="text-slate-400">→</span>
          </Link>
        ))}
      </div>
    )}
  </section>
);

export const InstituicaoDetalhe: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const instId = Number(id);

  const { data: inst, isLoading, isError } = useQuery({
    queryKey: ['instituicao', instId],
    queryFn: () => getInstituicao(instId),
    enabled: Number.isFinite(instId),
  });

  if (isLoading) return <DetailSkeleton />;

  if (isError || !inst) {
    return (
      <div className="p-10 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700">
        Instituição não encontrada.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <Link to="/governo" className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900">
        <ArrowLeft className="w-4 h-4" />
        Voltar ao mapa institucional
      </Link>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 md:p-8 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex flex-wrap gap-2 mb-2">
                {inst.sigla && (
                  <span className="px-2 py-0.5 rounded bg-slate-100 text-xs font-bold text-slate-700">{inst.sigla}</span>
                )}
                <span className="px-2 py-0.5 rounded bg-slate-100 text-xs font-medium text-slate-600">{inst.tipo}</span>
                <span className="px-2 py-0.5 rounded bg-slate-100 text-xs font-medium text-slate-600">{inst.esfera}</span>
              </div>
              <h1 className="text-2xl md:text-4xl font-extrabold tracking-tight text-slate-900">{inst.nome}</h1>
              <p className="text-sm text-slate-500 mt-2">{inst.poder} • {inst.nivel_federativo}</p>
            </div>
          </div>

          {inst.site_oficial && (
            <a
              href={inst.site_oficial}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Site oficial <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>

        {inst.descricao && (
          <p className="mt-6 pt-6 border-t border-slate-100 text-sm leading-relaxed text-slate-600 max-w-4xl">
            {inst.descricao}
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="rounded-xl bg-slate-50 p-4">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Natureza</div>
            <div className="text-sm font-semibold text-slate-800 mt-1">{inst.natureza_juridica || 'Não informada'}</div>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Fonte</div>
            <div className="text-sm font-semibold text-slate-800 mt-1">{inst.fonte}</div>
          </div>
          <div className="rounded-xl bg-slate-50 p-4">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Código externo</div>
            <div className="text-sm font-semibold text-slate-800 mt-1">{inst.codigo_externo || 'Não informado'}</div>
          </div>
        </div>

        {inst.url_fonte && (
          <a
            href={inst.url_fonte}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 underline"
          >
            Abrir fonte oficial <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </section>

      {inst.integrado && inst.estatisticas_camara && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Landmark className="w-5 h-5 text-slate-700" />
            <h2 className="text-lg font-bold text-slate-900">Integração com a Câmara dos Deputados</h2>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <Users className="w-4 h-4 text-slate-400 mb-2" />
              <div className="text-2xl font-extrabold">{inst.estatisticas_camara.total_deputados}</div>
              <div className="text-xs text-slate-500">Deputados na base</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <FileText className="w-4 h-4 text-slate-400 mb-2" />
              <div className="text-2xl font-extrabold">{inst.estatisticas_camara.total_proposicoes}</div>
              <div className="text-xs text-slate-500">Proposições</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <Vote className="w-4 h-4 text-slate-400 mb-2" />
              <div className="text-2xl font-extrabold">{inst.estatisticas_camara.total_votacoes}</div>
              <div className="text-xs text-slate-500">Votações</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <Database className="w-4 h-4 text-slate-400 mb-2" />
              <div className="text-2xl font-extrabold">{inst.estatisticas_camara.total_legislaturas}</div>
              <div className="text-xs text-slate-500">Legislaturas</div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {inst.estatisticas_camara.links.map((link) => (
              <Link key={link.url} to={link.url} className="px-4 py-2 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800">
                {link.label}
              </Link>
            ))}
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <RelationList
          title="Integra / responde a"
          items={inst.superiores}
          icon={<GitBranch className="w-4 h-4 text-slate-500" />}
        />
        <RelationList
          title="Unidades subordinadas"
          items={inst.subordinados}
          icon={<GitBranch className="w-4 h-4 text-slate-500" />}
        />
        <RelationList
          title="Instituições vinculadas"
          items={inst.vinculados}
          icon={<Link2 className="w-4 h-4 text-slate-500" />}
        />
      </div>

      {inst.relacoes.length > 0 && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <h2 className="font-bold text-slate-900 mb-4">Relações institucionais registradas</h2>
          <div className="space-y-3">
            {inst.relacoes.map((rel) => {
              const outgoing = rel.origem_id === inst.id;
              const otherName = outgoing ? rel.destino_nome : rel.origem_nome;
              const otherId = outgoing ? rel.destino_id : rel.origem_id;
              return (
                <div key={rel.id} className="rounded-xl border border-slate-100 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600 px-2 py-1 rounded">
                      {rel.tipo_relacao.replaceAll('_', ' ')}
                    </span>
                    <Link to={`/governo/instituicoes/${otherId}`} className="text-sm font-semibold text-slate-800 hover:text-blue-600">
                      {otherName}
                    </Link>
                  </div>
                  {rel.descricao && <p className="text-xs text-slate-500 mt-2">{rel.descricao}</p>}
                  {rel.fonte && <p className="text-[11px] text-slate-400 mt-2">Fonte: {rel.fonte}</p>}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
};
