import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, RefreshCw, ShieldAlert, Check, X, Clock } from 'lucide-react';
import { apiClient } from '../api/client';
import { Incident } from '../types';

export const IncidentDetails: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getIncidents({ limit: 50 });
      setIncidents(data);
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const handleApprove = async (incident: Incident) => {
    setActionLoading(incident.id);
    try {
      await apiClient.approveDecision(incident.id, 'Approved via Incident Dashboard');
      await fetchIncidents();
    } catch (err: any) {
      alert(err.message || 'Approval failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (incident: Incident) => {
    setActionLoading(incident.id);
    try {
      await apiClient.rejectDecision(incident.id, 'Rejected via Incident Dashboard');
      await fetchIncidents();
    } catch (err: any) {
      alert(err.message || 'Rejection failed');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle className="w-3 h-3" /> Approved
          </span>
        );
      case 'REJECTED':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
            <XCircle className="w-3 h-3" /> Rejected
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Pending Review
          </span>
        );
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Security & Policy Incidents
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Review high-risk policy violations, unauthorized refund proposals, fraud reports, and human escalation queues.
          </p>
        </div>

        <button
          onClick={fetchIncidents}
          disabled={loading}
          className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition w-fit"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {incidents.length === 0 && !loading && (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
          <CheckCircle className="w-10 h-10 mx-auto text-emerald-500/50 mb-2" />
          <p className="text-sm font-semibold text-slate-300">No active incidents</p>
          <p className="text-xs text-slate-500 mt-1">All customer interactions are operating within normal policy bounds.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {incidents.map((inc) => (
          <div
            key={inc.id}
            className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3.5 flex flex-col justify-between"
          >
            <div className="space-y-3">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 mono">
                    {inc.policy_id}
                  </span>
                  {getStatusBadge(inc.escalation_status)}
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded font-semibold ${
                  inc.severity === 'CRITICAL' ? 'bg-red-900/40 text-red-300 border border-red-700/50' :
                  'bg-rose-900/30 text-rose-300 border border-rose-700/40'
                }`}>
                  {inc.severity}
                </span>
              </div>

              {/* Reason */}
              <p className="text-xs font-semibold text-slate-200">{inc.reason}</p>

              {/* Message */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-xs">
                <span className="text-slate-500 font-semibold block mb-0.5">Original Customer Message:</span>
                <p className="text-slate-100">{inc.customer_message}</p>
              </div>

              {/* Proposal */}
              {inc.agent_a_proposal && (
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-xs">
                  <span className="text-slate-500 font-semibold block mb-0.5">Agent A Proposed Tool:</span>
                  <pre className="text-amber-300 mono text-[11px]">
                    {JSON.stringify(inc.agent_a_proposal, null, 2)}
                  </pre>
                </div>
              )}

              {/* Evidence */}
              {inc.evidence && (
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-xs">
                  <span className="text-slate-500 font-semibold block mb-0.5">Gateway Evidence:</span>
                  <pre className="text-slate-300 mono text-[11px]">
                    {JSON.stringify(inc.evidence, null, 2)}
                  </pre>
                </div>
              )}

              {/* Safe response */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-xs">
                <span className="text-slate-500 font-semibold block mb-0.5">Safe Response Enforced:</span>
                <p className="text-indigo-300 italic">{inc.safe_response || 'Standard policy response applied.'}</p>
              </div>
            </div>

            {/* Bottom Controls */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-500 mono">{new Date(inc.created_at).toLocaleString()}</span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleApprove(inc)}
                  disabled={actionLoading === inc.id || inc.escalation_status === 'APPROVED'}
                  className={`px-3 py-1.5 rounded-lg font-medium border transition flex items-center gap-1 ${
                    inc.escalation_status === 'APPROVED'
                      ? 'bg-emerald-950/40 text-emerald-600 border-emerald-900/40 cursor-not-allowed'
                      : 'bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 border-emerald-500/30'
                  }`}
                >
                  <Check className="w-3.5 h-3.5" /> Approve
                </button>
                <button
                  onClick={() => handleReject(inc)}
                  disabled={actionLoading === inc.id || inc.escalation_status === 'REJECTED'}
                  className={`px-3 py-1.5 rounded-lg font-medium border transition flex items-center gap-1 ${
                    inc.escalation_status === 'REJECTED'
                      ? 'bg-rose-950/40 text-rose-600 border-rose-900/40 cursor-not-allowed'
                      : 'bg-rose-600/20 hover:bg-rose-600/40 text-rose-400 border-rose-500/30'
                  }`}
                >
                  <X className="w-3.5 h-3.5" /> Reject
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
