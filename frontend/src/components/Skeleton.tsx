import React from 'react';

export const CardSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs animate-pulse">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-slate-200" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-200 rounded w-3/4" />
              <div className="h-3 bg-slate-200 rounded w-1/2" />
            </div>
          </div>
          <div className="space-y-2 pt-2">
            <div className="h-3 bg-slate-200 rounded w-full" />
            <div className="h-3 bg-slate-200 rounded w-5/6" />
          </div>
        </div>
      ))}
    </div>
  );
};

export const DetailSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-6">
      <div className="flex items-center space-x-5">
        <div className="w-20 h-20 rounded-full bg-slate-200" />
        <div className="flex-1 space-y-3">
          <div className="h-6 bg-slate-200 rounded w-1/3" />
          <div className="h-4 bg-slate-200 rounded w-1/4" />
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 bg-slate-100 rounded-lg" />
        ))}
      </div>
      <div className="h-64 bg-slate-100 rounded-lg pt-4" />
    </div>
  );
};
