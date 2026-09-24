import React from 'react';

interface VoteBadgeProps {
  tipo: string;
  size?: 'sm' | 'md';
}

export const VoteBadge: React.FC<VoteBadgeProps> = ({ tipo, size = 'md' }) => {
  const t = tipo.trim().toUpperCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  if (t === 'SIM') {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold';
  } else if (t === 'NÃO' || t === 'NAO') {
    colorClasses = 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
  } else if (t.includes('ABST')) {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 font-medium';
  } else if (t.includes('OBST')) {
    colorClasses = 'bg-purple-50 text-purple-700 border-purple-200 font-medium';
  } else if (t.includes('ARTIGO 17')) {
    colorClasses = 'bg-slate-100 text-slate-600 border-slate-300';
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center rounded-md border ${colorClasses} ${sizeClasses}`}>
      {tipo}
    </span>
  );
};

interface StatusBadgeProps {
  situacao: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ situacao }) => {
  const s = situacao.toLowerCase();

  let color = 'bg-slate-100 text-slate-700 border-slate-200';
  if (s.includes('aprovad') || s.includes('promulgad') || s.includes('exercício') || s.includes('norma jurídica')) {
    color = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (s.includes('rejeitad') || s.includes('arquivad')) {
    color = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (s.includes('urgência') || s.includes('pauta')) {
    color = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (s.includes('tramitação') || s.includes('comissão')) {
    color = 'bg-amber-50 text-amber-800 border-amber-200';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${color}`}>
      {situacao}
    </span>
  );
};
