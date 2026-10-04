export type DecisionType = 'ALLOW' | 'MODIFY' | 'BLOCK' | 'ESCALATE';
export type SeverityType = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ProposedAction {
  tool_name: string;
  arguments: Record<string, any>;
}

export interface AuthorizationEnvelope {
  decision_id: string;
  request_id: string;
  allowed_agent: string;
  allowed_tool: string;
  allowed_arguments: Record<string, any>;
  policy_id: string;
  policy_version: string;
}

export interface ConversationContext {
  conversation_id: string;
  customer_id: string;
  customer_verified: boolean;
  verified_at?: string | null;
  previous_refunds: Array<{ order_id: string; amount: number; timestamp: string }>;
  complaint_count: number;
  order_lookups: Record<string, any>;
  last_updated_at: string;
}

export interface ChatResponse {
  request_id: string;
  conversation_id: string;
  policy_version: string;
  decision: DecisionType;
  severity: SeverityType;
  policy_id: string | null;
  reason: string;
  evidence: Record<string, any>;
  proposed_action: ProposedAction | null;
  approved_action: AuthorizationEnvelope | null;
  safe_response: string | null;
  requires_human_review: boolean;
  tool_executed: boolean;
  tool_result: Record<string, any> | null;
  final_response: string;
  agent_a_response: string | null;
  original_response?: string | null;
  corrected_response?: string | null;
  remediation_type?: 'TEMPLATE' | 'LLM' | null;
  agent_b_called: boolean;
  incident_id: string | null;
  context?: ConversationContext | null;
}

export interface AuditEvent {
  id: string;
  request_id: string;
  conversation_id: string;
  customer_id: string;
  customer_message: string;
  agent_a_response: string | null;
  proposed_action: Record<string, any> | null;
  agent_b_action: Record<string, any> | null;
  policy_id: string | null;
  policy_version: string | null;
  severity: string | null;
  evidence: Record<string, any> | null;
  decision: DecisionType;
  safe_response: string | null;
  tool_executed: boolean;
  tool_result: Record<string, any> | null;
  escalation_status: string | null;
  timestamp: string;
}

export interface Incident {
  id: string;
  request_id: string;
  conversation_id: string;
  customer_id: string;
  customer_message: string;
  agent_a_proposal: Record<string, any> | null;
  policy_id: string;
  severity: SeverityType;
  reason: string;
  evidence: Record<string, any> | null;
  decision: DecisionType;
  safe_response: string | null;
  escalation_status: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyVersion {
  id: string;
  policy_id: string;
  version: string;
  definition_yaml: string;
  is_active: boolean;
  created_at: string;
}

export interface Policy {
  policy_id: string;
  name: string;
  description: string;
  severity: SeverityType;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  versions: PolicyVersion[];
}
