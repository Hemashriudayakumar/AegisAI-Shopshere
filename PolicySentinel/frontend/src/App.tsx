import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { Simulator } from './components/Simulator';
import { AuditHistory } from './components/AuditHistory';
import { IncidentDetails } from './components/IncidentDetails';
import { PolicyList } from './components/PolicyList';
import { apiClient } from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'simulator' | 'audits' | 'incidents' | 'policies'>('simulator');
  const [incidentCount, setIncidentCount] = useState<number>(0);

  const refreshIncidentCount = async () => {
    try {
      const incidents = await apiClient.getIncidents({ limit: 100 });
      setIncidentCount(incidents.length);
    } catch (err) {
      // ignore
    }
  };

  useEffect(() => {
    refreshIncidentCount();
    const interval = setInterval(refreshIncidentCount, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        incidentCount={incidentCount}
      />

      <main className="flex-1 pb-16">
        {activeTab === 'simulator' && <Simulator onEventLogged={refreshIncidentCount} />}
        {activeTab === 'audits' && <AuditHistory />}
        {activeTab === 'incidents' && <IncidentDetails />}
        {activeTab === 'policies' && <PolicyList />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>AegisAI Gateway v1.0 • Built with LangGraph, Qwen3-8B & FastAPI</p>
      </footer>
    </div>
  );
};

export default App;
