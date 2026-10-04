import React, { useEffect, useState } from 'react';
import { Shield, Activity, FileText, AlertTriangle, Cpu, Radio } from 'lucide-react';
import { apiClient } from '../api/client';

interface NavbarProps {
  activeTab: 'simulator' | 'audits' | 'incidents' | 'policies';
  setActiveTab: (tab: 'simulator' | 'audits' | 'incidents' | 'policies') => void;
  incidentCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, incidentCount = 0 }) => {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await apiClient.getHealth();
        setHealth(data);
      } catch (e) {
        // ignore
      }
    };
    fetchHealth();
    const timer = setInterval(fetchHealth, 10000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">AegisAI</span>
              {health?.ollama_connected ? (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Ollama ({health.model})
                </span>
              ) : (
                <span
                  title="Ollama is not running locally. Intelligent Fallback Provider is handling responses."
                  className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 font-medium flex items-center gap-1"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  Fallback Mode (Ollama Offline)
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">AI Customer-Support Policy Enforcement</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'simulator'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Simulator</span>
          </button>

          <button
            onClick={() => setActiveTab('audits')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'audits'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Audit History</span>
          </button>

          <button
            onClick={() => setActiveTab('incidents')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all relative ${
              activeTab === 'incidents'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Incidents</span>
            {incidentCount > 0 && (
              <span className="w-5 h-5 rounded-full bg-rose-500 text-white text-xs flex items-center justify-center font-bold">
                {incidentCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('policies')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'policies'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Policies</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
