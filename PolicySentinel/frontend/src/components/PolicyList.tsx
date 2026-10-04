import React, { useEffect, useState } from 'react';
import { Cpu, Edit3, Plus, RefreshCw, Check, Code, ShieldCheck } from 'lucide-react';
import { apiClient } from '../api/client';
import { Policy } from '../types';

export const PolicyList: React.FC = () => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [yamlContent, setYamlContent] = useState('');
  const [newVersion, setNewVersion] = useState('v1.1');
  const [updating, setUpdating] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchPolicies = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getPolicies();
      setPolicies(data);
      if (data.length > 0 && !selectedPolicy) {
        setSelectedPolicy(data[0]);
        setYamlContent(data[0].versions[0]?.definition_yaml || '');
      }
    } catch (err) {
      console.error('Failed to load policies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleSelect = (pol: Policy) => {
    setSelectedPolicy(pol);
    setYamlContent(pol.versions[0]?.definition_yaml || '');
    setSuccessMsg(null);
  };

  const handleSaveVersion = async () => {
    if (!selectedPolicy) return;
    setUpdating(true);
    setSuccessMsg(null);

    try {
      await apiClient.updatePolicy(selectedPolicy.policy_id, {
        version: newVersion,
        definition_yaml: yamlContent,
      });
      setSuccessMsg(`Policy ${selectedPolicy.policy_id} updated to version ${newVersion} successfully!`);
      await fetchPolicies();
    } catch (err: any) {
      alert(err.message || 'Failed to save policy version');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            Active Policy Rules & Version Registry
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Manage deterministic YAML policy definitions, parameters, thresholds, and version history.
          </p>
        </div>

        <button
          onClick={fetchPolicies}
          disabled={loading}
          className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition w-fit"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Policy Cards List */}
        <div className="lg:col-span-5 space-y-3">
          {policies.map((pol) => (
            <div
              key={pol.policy_id}
              onClick={() => handleSelect(pol)}
              className={`p-4 rounded-xl border transition cursor-pointer flex flex-col justify-between ${
                selectedPolicy?.policy_id === pol.policy_id
                  ? 'bg-indigo-600/15 border-indigo-500/50 shadow-lg shadow-indigo-600/10'
                  : 'bg-slate-900/80 border-slate-800 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="mono text-xs font-bold text-indigo-400">{pol.policy_id}</span>
                <span className="text-[11px] px-2 py-0.5 rounded font-semibold bg-slate-800 text-slate-300">
                  {pol.versions[0]?.version || 'v1.0'}
                </span>
              </div>
              <h4 className="text-xs font-semibold text-white mt-1.5">{pol.name}</h4>
              <p className="text-xs text-slate-400 line-clamp-2 mt-1">{pol.description}</p>
              
              <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                <span className="text-emerald-400 flex items-center gap-1 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5" /> Enforced Active
                </span>
                <span className="text-slate-500 font-semibold">{pol.severity}</span>
              </div>
            </div>
          ))}
        </div>

        {/* YAML Definition Editor */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Code className="w-4 h-4 text-indigo-400" />
                Policy Definition Editor: {selectedPolicy?.policy_id}
              </h3>
              <p className="text-xs text-slate-400">{selectedPolicy?.name}</p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Target Version:</span>
              <input
                type="text"
                value={newVersion}
                onChange={(e) => setNewVersion(e.target.value)}
                className="w-16 bg-slate-950 border border-slate-800 px-2 py-1 text-xs rounded text-slate-200 mono text-center"
              />
            </div>
          </div>

          <div>
            <textarea
              value={yamlContent}
              onChange={(e) => setYamlContent(e.target.value)}
              rows={14}
              className="w-full rounded-xl bg-slate-950 border border-slate-800 p-3.5 text-xs text-emerald-300 mono focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>

          {successMsg && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
              <Check className="w-4 h-4 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleSaveVersion}
              disabled={updating}
              className="py-2.5 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition disabled:opacity-50"
            >
              {updating ? 'Saving Version...' : 'Deploy Policy Version'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
