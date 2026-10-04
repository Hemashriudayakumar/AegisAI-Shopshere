from typing import Any, Dict, Optional, TypedDict
from app.schemas.chat import (
    AgentAResponse,
    AgentBAction,
    AuthorizationEnvelope,
    PolicyDecision,
    ProposedAction,
)

class PolicyState(TypedDict, total=False):
    request_id: str
    conversation_id: str
    customer_id: str
    customer_message: str
    conversation_context: Dict[str, Any]
    context_data: Optional[Dict[str, Any]]
    
    agent_a_response: Optional[str]
    proposed_action: Optional[Dict[str, Any]]
    
    policy_decision: Optional[Dict[str, Any]]
    approved_action: Optional[Dict[str, Any]]
    
    agent_b_action: Optional[Dict[str, Any]]
    agent_b_called: bool
    
    tool_executed: bool
    tool_result: Optional[Dict[str, Any]]
    
    original_response: Optional[str]
    corrected_response: Optional[str]
    remediation_type: Optional[str]
    
    final_response: Optional[str]
    audit_event: Optional[Dict[str, Any]]
    incident_id: Optional[str]
    error: Optional[str]
