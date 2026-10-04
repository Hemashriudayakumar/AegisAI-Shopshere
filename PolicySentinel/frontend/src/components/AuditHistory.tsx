import React, { useEffect, useState } from 'react';
import { FileText, RefreshCw, Eye, CheckCircle, XCircle, AlertTriangle, Sparkles } from 'lucide-react';
import { apiClient } from '../api/client';
import { AuditEvent, DecisionType } from '../types';

export const AuditHistory: React.FC = () => {
  const [audits, setAudits] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterDecision, setFilterDecision] = useState<string>('');
  const [selectedAudit, setSelectedAudit] = useState<AuditEvent | null>(null);

  const fetchAudits = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getAudits({
        decision: filterDecision || undefined,
        limit: 50,
      });
      setAudits(data);
    } catch (err) {
      console.error('Failed to load audits:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudits();
  }, [filterDecision]);

  const getDecisionBadge = (decision: DecisionType) => {
    switch (decision) {
      case 'ALLOW':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit"><CheckCircle className="w-3 h-3" /> ALLOW</span>;
      case 'MODIFY':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-fit"><Sparkles className="w-3 h-3" /> MODIFY</span>;
      case 'BLOCK':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1 w-fit"><XCircle className="w-3 h-3" /> BLOCK</span>;
      case 'ESCALATE':
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center gap-1 w-fit"><AlertTriangle className="w-3 h-3" /> ESCALATE</span>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            Immutable Audit Trail
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Every customer inquiry, agent proposal, gateway evaluation, and interceptor action is recorded immutably.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={filterDecision}
            onChange={(e) => setFilterDecision(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Decisions</option>
            <option value="ALLOW">ALLOW</option>
            <option value="MODIFY">MODIFY</option>
            <option value="BLOCK">BLOCK</option>
            <option value="ESCALATE">ESCALATE</option>
          </select>

          <button
            onClick={fetchAudits}
            disabled={loading}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Audit Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase font-semibold">
                <th className="py-3 px-4">Request ID</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4">Policy ID</th>
                <th className="py-3 px-4">Customer Query</th>
                <th className="py-3 px-4">Tool Executed</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {audits.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-500">
                    No audit records found.
                  </td>
                </tr>
              )}
              {audits.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3.5 px-4 mono text-indigo-400 font-semibold">{item.request_id}</td>
                  <td className="py-3.5 px-4">{getDecisionBadge(item.decision)}</td>
                  <td className="py-3.5 px-4 mono text-slate-300">{item.policy_id || 'NONE'}</td>
                  <td className="py-3.5 px-4 max-w-xs truncate text-slate-200" title={item.customer_message}>
                    {item.customer_message}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                      item.tool_executed ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'
                    }`}>
                      {item.tool_executed ? 'YES' : 'NO'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 mono">
                    {new Date(item.timestamp).toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => setSelectedAudit(item)}
                      className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 text-xs font-medium border border-indigo-500/30 transition flex items-center gap-1 ml-auto"
                    >
                      <Eye className="w-3.5 h-3.5" /> Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Detail Modal */}
      {selectedAudit && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  Audit Record: {selectedAudit.request_id}
                </h3>
                <p className="text-xs text-slate-400">Conversation: {selectedAudit.conversation_id} | Customer: {selectedAudit.customer_id}</p>
              </div>
              <button
                onClick={() => setSelectedAudit(null)}
                className="text-slate-400 hover:text-white text-sm font-bold px-2 py-1 bg-slate-800 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-1">Customer Query:</span>
                <p className="text-slate-100">{selectedAudit.customer_message}</p>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-1">Agent A Response:</span>
                <p className="text-slate-100">{selectedAudit.agent_a_response || 'None'}</p>
              </div>

              {selectedAudit.proposed_action && (
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-1">Proposed Action:</span>
                  <pre className="text-amber-300 mono bg-slate-900 p-2 rounded border border-slate-800">
                    {JSON.stringify(selectedAudit.proposed_action, null, 2)}
                  </pre>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-1">Policy ID & Version:</span>
                  <p className="text-slate-100 mono">{selectedAudit.policy_id} ({selectedAudit.policy_version})</p>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-1">Gateway Decision:</span>
                  <div>{getDecisionBadge(selectedAudit.decision)}</div>
                </div>
              </div>

              {selectedAudit.evidence && (
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-1">Evidence:</span>
                  <pre className="text-slate-300 mono bg-slate-900 p-2 rounded border border-slate-800">
                    {JSON.stringify(selectedAudit.evidence, null, 2)}
                  </pre>
                </div>
              )}

              {selectedAudit.tool_result && (
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-1">Tool Execution Result:</span>
                  <pre className="text-emerald-300 mono bg-slate-900 p-2 rounded border border-slate-800">
                    {JSON.stringify(selectedAudit.tool_result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
