import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Search, Building2, FileText, Users, Home, Menu, X } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/?q=${encodeURIComponent(searchQuery.trim())}`);
      setMobileMenuOpen(false);
    }
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-slate-100 text-slate-900 font-semibold'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
    }`;

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-xs border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo e Nome */}
          <div className="flex items-center gap-3">
            <NavLink to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-slate-900 flex items-center justify-center text-white shadow-xs group-hover:bg-slate-800 transition-colors">
                <Building2 className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold tracking-tight text-slate-900 leading-none">
                  Snitch
                </span>
                <span className="text-[11px] font-medium text-slate-500 tracking-wide uppercase mt-0.5">
                  Atividade Legislativa
                </span>
              </div>
            </NavLink>
          </div>

          {/* Links desktop */}
          <nav className="hidden md:flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              <Home className="w-4 h-4" />
              Visão Geral
            </NavLink>
            <NavLink to="/proposicoes" className={navLinkClass}>
              <FileText className="w-4 h-4" />
              Proposições
            </NavLink>
            <NavLink to="/deputados" className={navLinkClass}>
              <Users className="w-4 h-4" />
              Deputados
            </NavLink>
          </nav>

          {/* Busca rápida e badge */}
          <div className="hidden lg:flex items-center gap-4">
            <form onSubmit={handleSearchSubmit} className="relative w-64">
              <input
                type="text"
                placeholder="Buscar PL ou Deputado..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400 transition-all"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2 pointer-events-none" />
            </form>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200 select-none">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Dados Oficiais
            </span>
          </div>

          {/* Botão Mobile */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              aria-label="Abrir menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Menu mobile */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-5 space-y-3">
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              placeholder="Buscar PL ou Deputado..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 placeholder-slate-400"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
          </form>
          <div className="flex flex-col space-y-1">
            <NavLink
              to="/"
              end
              onClick={() => setMobileMenuOpen(false)}
              className={navLinkClass}
            >
              <Home className="w-4 h-4" />
              Visão Geral
            </NavLink>
            <NavLink
              to="/proposicoes"
              onClick={() => setMobileMenuOpen(false)}
              className={navLinkClass}
            >
              <FileText className="w-4 h-4" />
              Proposições
            </NavLink>
            <NavLink
              to="/deputados"
              onClick={() => setMobileMenuOpen(false)}
              className={navLinkClass}
            >
              <Users className="w-4 h-4" />
              Deputados
            </NavLink>
          </div>
        </div>
      )}
    </header>
  );
};
