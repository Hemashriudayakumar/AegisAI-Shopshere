import { AuditEvent, ChatResponse, ConversationContext, Incident, Policy } from '../types';

const getApiBase = () => {
  if (typeof window !== 'undefined') {
    // If the frontend is served on a different port than 8000 (e.g. 5173), direct calls to 127.0.0.1:8000 avoid proxy issues
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      if (window.location.port !== '8000') {
        return 'http://127.0.0.1:8000/api';
      }
    }
  }
  return '/api';
};

const API_BASE = getApiBase();

export const apiClient = {
  async sendChatMessage(payload: {
    customer_message: string;
    customer_id?: string;
    conversation_id?: string;
    is_verified?: boolean;
    manager_approved?: boolean;
  }): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Network request failed' }));
      throw new Error(err.detail || 'Chat request failed');
    }
    return res.json();
  },

  async getChatContext(conversationId: string): Promise<ConversationContext> {
    const res = await fetch(`${API_BASE}/chat/context/${conversationId}`);
    if (!res.ok) throw new Error('Failed to fetch conversation context');
    return res.json();
  },

  async getAudits(params?: { limit?: number; offset?: number; decision?: string }): Promise<AuditEvent[]> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));
    if (params?.decision) query.append('decision', params.decision);

    const res = await fetch(`${API_BASE}/audits?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch audits');
    return res.json();
  },

  async getIncidents(params?: { limit?: number; status?: string }): Promise<Incident[]> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.status) query.append('status', params.status);

    const res = await fetch(`${API_BASE}/incidents?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch incidents');
    return res.json();
  },

  async getPolicies(): Promise<Policy[]> {
    const res = await fetch(`${API_BASE}/policies`);
    if (!res.ok) throw new Error('Failed to fetch policies');
    return res.json();
  },

  async updatePolicy(policyId: string, payload: { version: string; definition_yaml: string; description?: string }): Promise<Policy> {
    const res = await fetch(`${API_BASE}/policies/${policyId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update policy');
    return res.json();
  },

  async approveDecision(decisionId: string, notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/approvals/${decisionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_notes: notes }),
    });
    if (!res.ok) throw new Error('Failed to approve action');
    return res.json();
  },

  async rejectDecision(decisionId: string, notes?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/approvals/${decisionId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_notes: notes }),
    });
    if (!res.ok) throw new Error('Failed to reject action');
    return res.json();
  },

  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  }
};
