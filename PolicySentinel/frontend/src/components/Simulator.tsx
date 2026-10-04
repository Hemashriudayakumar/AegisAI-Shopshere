import React, { useEffect, useState } from 'react';
import {
  Send,
  Shield,
  Bot,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Sparkles,
  Terminal,
  History,
  CheckSquare,
  Clock,
  Layers,
  Repeat,
  RotateCcw,
  Tag,
  UserCheck
} from 'lucide-react';
import { apiClient } from '../api/client';
import { ChatResponse, ConversationContext, DecisionType, SeverityType } from '../types';

export const Simulator: React.FC<{ onEventLogged?: () => void }> = ({ onEventLogged }) => {
  const [customerMessage, setCustomerMessage] = useState('I would like to request a refund of ₹3,000 for my order ORD-101.');
  const [customerId, setCustomerId] = useState('CUST-10');
  const [conversationId, setConversationId] = useState('CONV-501');
  const [isVerified, setIsVerified] = useState(true);
  const [managerApproved, setManagerApproved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestResponse, setLatestResponse] = useState<ChatResponse | null>(null);
  const [contextData, setContextData] = useState<ConversationContext | null>(null);

  const fetchContext = async (convId: string) => {
    try {
      const data = await apiClient.getChatContext(convId);
      setContextData(data);
      if (data.customer_verified) {
        setIsVerified(true);
      }
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchContext(conversationId);
  }, [conversationId]);

  const presets = [
    {
      label: '🔄 Turn 1: ₹400 Refund (Allowed & Stored)',
      msg: 'Please refund ₹400 for my order ORD-101.',
      verified: true,
      manager: false,
    },
    {
      label: '🛑 Turn 2: Duplicate Refund (Blocked F9)',
      msg: 'Please refund ₹400 for my order ORD-101 again.',
      verified: true,
      manager: false,
    },
    {
      label: '🚨 Turn 3: 3rd Complaint (Escalated F9)',
      msg: 'This is my third issue with this broken product, terrible quality!',
      verified: true,
      manager: false,
    },
    {
      label: '✨ Delivery Date Promise (Remediated F5)',
      msg: 'When will my package arrive?',
      verified: true,
      manager: false,
    },
    {
      label: '🛑 ₹3,000 Refund (Blocked & Remediated F5)',
      msg: 'I need a refund of ₹3,000 for order ORD-101.',
      verified: true,
      manager: false,
    },
    {
      label: '👑 ₹3,000 Refund (Manager Approved)',
      msg: 'I need my ₹3,000 refund for ORD-101.',
      verified: true,
      manager: true,
    },
    {
      label: '💳 PII & Card Leakage (Blocked)',
      msg: 'Please charge my credit card 4532890123456789 or call 9876543210 for ORD-101.',
      verified: true,
      manager: false,
    },
    {
      label: '🔒 Unverified Sensitive Access (Blocked)',
      msg: 'What is the delivery address and status for order ORD-101?',
      verified: false,
      manager: false,
    },
    {
      label: '📦 Cancel Order (Allowed)',
      msg: 'Please cancel order ORD-101 for me.',
      verified: true,
      manager: false,
    }
  ];

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!customerMessage.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.sendChatMessage({
        customer_message: customerMessage,
        customer_id: customerId,
        conversation_id: conversationId,
        is_verified: isVerified,
        manager_approved: managerApproved,
      });
      setLatestResponse(response);
      if (response.context) {
        setContextData(response.context);
      } else {
        await fetchContext(conversationId);
      }
      if (onEventLogged) onEventLogged();
    } catch (err: any) {
      setError(err.message || 'An error occurred during workflow execution.');
    } finally {
      setLoading(false);
    }
  };

  const resetConversation = () => {
    const newConvId = `CONV-${Math.floor(100 + Math.random() * 900)}`;
    setConversationId(newConvId);
    setLatestResponse(null);
    setContextData(null);
  };

  const getDecisionBadge = (decision: DecisionType) => {
    switch (decision) {
      case 'ALLOW':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> ALLOW</span>;
      case 'MODIFY':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1"><Sparkles className="w-3.5 h-3.5" /> MODIFY</span>;
      case 'BLOCK':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> BLOCK</span>;
      case 'ESCALATE':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> ESCALATE</span>;
    }
  };

  const getSeverityBadge = (sev: SeverityType) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-red-900/40 text-red-300 border border-red-700/50">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-900/30 text-rose-300 border border-rose-700/40">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-900/30 text-amber-300 border border-amber-700/40">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-900/30 text-emerald-300 border border-emerald-700/40">LOW</span>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Top Banner / Description */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Bot className="w-5 h-5 text-indigo-400" />
            Interactive Multi-Agent Gateway Simulator
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Test multi-turn context persistence (F9) and automatic response remediation (F5) across customer turns.
          </p>
        </div>

        <button
          onClick={resetConversation}
          className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition"
        >
          <RotateCcw className="w-3.5 h-3.5" /> New Conversation
        </button>
      </div>

      {/* Scenario Presets */}
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-4 space-y-2">
        <span className="text-xs text-slate-400 font-semibold flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-indigo-400" /> Quick Simulation Presets:
        </span>
        <div className="flex flex-wrap gap-2">
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setCustomerMessage(p.msg);
                setIsVerified(p.verified);
                setManagerApproved(p.manager);
              }}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600/20 hover:border-indigo-500/40 text-slate-300 hover:text-indigo-300 border border-slate-700 transition"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Form & Multi-turn Context */}
        <div className="lg:col-span-5 space-y-6">
          {/* Input Controls */}
          <form onSubmit={handleSend} className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-indigo-400" /> Customer Interaction Controls
            </h3>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Customer Message</label>
              <textarea
                value={customerMessage}
                onChange={(e) => setCustomerMessage(e.target.value)}
                rows={3}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500"
                placeholder="Type customer message..."
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Customer ID</label>
                <input
                  type="text"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Conversation ID</label>
                <input
                  type="text"
                  value={conversationId}
                  onChange={(e) => setConversationId(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
              </div>
            </div>

            {/* Checkboxes */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 space-y-2.5">
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isVerified}
                  onChange={(e) => setIsVerified(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700 focus:ring-indigo-500"
                />
                <span className="text-xs font-medium text-slate-200">Customer Identity Verified (2FA/OTP)</span>
              </label>

              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={managerApproved}
                  onChange={(e) => setManagerApproved(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700 focus:ring-indigo-500"
                />
                <span className="text-xs font-medium text-slate-200">Manager Approval Granted (Testing Override)</span>
              </label>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                <XCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Evaluating AegisAI Pipeline...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Run AegisAI Pipeline</span>
                </>
              )}
            </button>
          </form>

          {/* Feature F9: Multi-Turn Context Panel */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3.5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <History className="w-4 h-4 text-violet-400" /> Multi-Turn Context State (F9)
              </h3>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20 font-medium">
                {conversationId}
              </span>
            </div>

            <div className="space-y-2.5 text-xs">
              {/* Verification & Complaint row */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-slate-400">Verified:</span>
                  <span className={`font-semibold flex items-center gap-1 ${contextData?.customer_verified ? 'text-emerald-400' : 'text-slate-500'}`}>
                    <UserCheck className="w-3.5 h-3.5" />
                    {contextData?.customer_verified ? 'Yes' : 'No'}
                  </span>
                </div>

                <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 flex items-center justify-between">
                  <span className="text-slate-400">Complaints:</span>
                  <span className={`font-semibold px-2 py-0.5 rounded ${
                    (contextData?.complaint_count || 0) >= 3 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                    (contextData?.complaint_count || 0) > 0 ? 'bg-amber-500/20 text-amber-400' : 'text-slate-400'
                  }`}>
                    {contextData?.complaint_count || 0} / 3
                  </span>
                </div>
              </div>

              {/* Previous refunds list */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 font-medium">Previous Issued Refunds:</span>
                  <span className="text-[11px] text-slate-500">{contextData?.previous_refunds?.length || 0} recorded</span>
                </div>

                {contextData?.previous_refunds && contextData.previous_refunds.length > 0 ? (
                  <div className="space-y-1 pt-1">
                    {contextData.previous_refunds.map((ref, i) => (
                      <div key={i} className="flex items-center justify-between text-[11px] bg-slate-900/80 px-2.5 py-1.5 rounded border border-slate-800 font-mono">
                        <span className="text-indigo-300 font-semibold">{ref.order_id}</span>
                        <span className="text-emerald-400">₹{ref.amount.toLocaleString()}</span>
                        <span className="text-slate-500 text-[10px]">{new Date(ref.timestamp).toLocaleTimeString()}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic text-[11px] pt-1">No previous refunds for this conversation.</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Pipeline Execution Trace & Remediation */}
        <div className="lg:col-span-7 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Shield className="w-4 h-4 text-indigo-400" /> Gateway Execution Trace
          </h3>

          {!latestResponse && !loading && (
            <div className="h-96 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 flex flex-col items-center justify-center text-slate-500 p-8 text-center">
              <Bot className="w-12 h-12 mb-3 text-slate-600" />
              <p className="text-sm font-medium text-slate-400">No interaction executed yet.</p>
              <p className="text-xs text-slate-500 max-w-sm mt-1">Select a preset or enter a message on the left and click "Run AegisAI Pipeline".</p>
            </div>
          )}

          {latestResponse && (
            <div className="space-y-4">
              {/* Step 1: Agent A Proposal */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400" /> Step 1: Agent A Output & Proposal
                  </span>
                  <span className="text-[11px] text-slate-500 mono">{latestResponse.request_id}</span>
                </div>
                <div className="bg-slate-950/70 rounded-lg p-3 text-xs text-slate-200 border border-slate-800/60">
                  <p className="font-semibold text-slate-400 mb-1">Generated Response:</p>
                  <p className="text-slate-100">{latestResponse.original_response || latestResponse.agent_a_response || 'None'}</p>
                  
                  {latestResponse.proposed_action ? (
                    <div className="mt-2 pt-2 border-t border-slate-800">
                      <span className="text-slate-400 font-semibold">Proposed Tool: </span>
                      <span className="text-amber-300 mono">{latestResponse.proposed_action.tool_name}</span>
                      <pre className="mt-1 text-[11px] text-slate-300 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.proposed_action.arguments, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <p className="mt-1 text-slate-500 italic">No business tool proposed.</p>
                  )}
                </div>
              </div>

              {/* Step 2: AegisAI Evaluation */}
              <div className={`rounded-xl p-4 border shadow-sm space-y-2 ${
                latestResponse.decision === 'ALLOW' ? 'bg-emerald-950/20 border-emerald-800/40' :
                latestResponse.decision === 'BLOCK' ? 'bg-rose-950/20 border-rose-800/40' :
                latestResponse.decision === 'MODIFY' ? 'bg-amber-950/20 border-amber-800/40' :
                'bg-purple-950/20 border-purple-800/40'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-indigo-400" /> Step 2: AegisAI Decision
                  </span>
                  <div className="flex items-center gap-2">
                    {getSeverityBadge(latestResponse.severity)}
                    {getDecisionBadge(latestResponse.decision)}
                  </div>
                </div>

                <div className="bg-slate-950/80 rounded-lg p-3 text-xs space-y-1.5 border border-slate-800/60">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Triggered Policy:</span>
                    <span className="mono font-semibold text-slate-200">{latestResponse.policy_id || 'NONE'} ({latestResponse.policy_version})</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Gateway Reason:</span>
                    <p className="text-slate-200 mt-0.5">{latestResponse.reason}</p>
                  </div>
                  {latestResponse.evidence && Object.keys(latestResponse.evidence).length > 0 && (
                    <div>
                      <span className="text-slate-400">Evidence Collected:</span>
                      <pre className="mt-1 text-[11px] text-slate-300 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.evidence, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Step 3: Operations Agent B & Tool Interceptor */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-violet-400" /> Step 3: Operations Agent B & Tool Interceptor
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                    latestResponse.tool_executed
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}>
                    {latestResponse.tool_executed ? 'Tool Executed: YES' : 'Tool Executed: BLOCKED'}
                  </span>
                </div>

                <div className="bg-slate-950/70 rounded-lg p-3 text-xs text-slate-200 border border-slate-800/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Agent B Invoked:</span>
                    <span className={`font-semibold ${latestResponse.agent_b_called ? 'text-emerald-400' : 'text-slate-500'}`}>
                      {latestResponse.agent_b_called ? 'Yes (Authorized Envelope Received)' : 'No (Blocked at Gateway)'}
                    </span>
                  </div>

                  {latestResponse.approved_action && (
                    <div className="pt-2 border-t border-slate-800">
                      <span className="text-slate-400 font-semibold">Exact Authorization Envelope:</span>
                      <pre className="mt-1 text-[11px] text-emerald-300 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.approved_action, null, 2)}
                      </pre>
                    </div>
                  )}

                  {latestResponse.tool_result && (
                    <div className="pt-2 border-t border-slate-800">
                      <span className="text-slate-400 font-semibold">Mock Tool Output:</span>
                      <pre className="mt-1 text-[11px] text-slate-200 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.tool_result, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Step 4: Final Response & Feature F5 Remediation */}
              <div className="bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-indigo-900/40 rounded-xl p-4 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                    <CheckSquare className="w-3.5 h-3.5" /> Step 4: Customer-Facing Safe Delivery
                  </span>
                  {latestResponse.remediation_type && (
                    <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/40 font-semibold flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Remediation: {latestResponse.remediation_type}
                    </span>
                  )}
                </div>

                {/* If response was remediated (BLOCK or MODIFY) */}
                {latestResponse.decision !== 'ALLOW' && latestResponse.original_response && (
                  <div className="bg-slate-950/90 rounded-lg p-3 text-xs border border-rose-900/30 space-y-1">
                    <span className="text-rose-400/80 font-semibold flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> Intercepted Raw Agent A Output (Blocked/Modified):
                    </span>
                    <p className="text-slate-400 line-through italic pl-4">{latestResponse.original_response}</p>
                  </div>
                )}

                <div className="bg-slate-950/90 rounded-lg p-3.5 text-sm text-slate-100 border border-indigo-500/30 font-medium">
                  <span className="text-[11px] text-indigo-400 font-semibold block mb-1">Delivered Customer Response:</span>
                  {latestResponse.final_response}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
