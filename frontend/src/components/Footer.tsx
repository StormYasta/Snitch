import React from 'react';
import { Link } from 'react-router-dom';
import { Database, ExternalLink, ShieldCheck } from 'lucide-react';

interface FooterProps {
  ultimaSincronizacao?: string | null;
}

export const Footer: React.FC<FooterProps> = ({ ultimaSincronizacao }) => {
  return (
    <footer className="mt-20 border-t border-slate-200 bg-white py-10 text-slate-500 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-slate-400" />
            <span className="font-medium text-slate-700">Fonte dos Dados:</span>
            <span>Câmara dos Deputados — Dados Abertos (API v2) • SIORG — Estrutura do Executivo Federal</span>
            <Link
              to="/fontes"
              className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 underline ml-1"
            >
              Ver todas as fontes e datas de acesso
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>

          {ultimaSincronizacao && (
            <div className="text-slate-500">
              Última sincronização: <span className="font-semibold text-slate-700">{ultimaSincronizacao}</span>
            </div>
          )}
        </div>

        <div className="pt-4 border-t border-slate-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-slate-400 text-[11px]">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-slate-400" />
            <span>
              Compromisso de Neutralidade: Esta aplicação não atribui notas, rankings ideológicos ou juízo de produtividade. Todos os registros refletem os dados públicos oficiais.
            </span>
          </div>
          <div>
            Snitch — Observatório da Atividade Legislativa © {new Date().getFullYear()}
          </div>
        </div>
      </div>
    </footer>
  );
};
