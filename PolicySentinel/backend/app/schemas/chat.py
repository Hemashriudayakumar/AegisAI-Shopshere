from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

DecisionType = Literal["ALLOW", "MODIFY", "BLOCK", "ESCALATE"]
SeverityType = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

class ProposedAction(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class AgentAResponse(BaseModel):
    response: str
    proposed_action: Optional[ProposedAction] = None


class AuthorizationEnvelope(BaseModel):
    decision_id: str
    request_id: str
    allowed_agent: str = "operations_agent"
    allowed_tool: str
    allowed_arguments: Dict[str, Any]
    policy_id: str
    policy_version: str


class PolicyDecision(BaseModel):
    decision: DecisionType
    policy_id: str
    policy_version: str
    severity: SeverityType
    risk_level: Optional[SeverityType] = None
    reason: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    requires_human_review: bool = False
    safe_response: Optional[str] = None
    modified_arguments: Optional[Dict[str, Any]] = None


class AgentBAction(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    customer_message: str
    customer_id: str = "CUST-10"
    conversation_id: Optional[str] = None
    is_verified: bool = False
    manager_approved: bool = False


class EvaluateRequest(BaseModel):
    agent_id: Optional[str] = "customer-service-agent"
    customer_id: str = "CUS1001"
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    risk_level: Optional[str] = "MEDIUM"
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_verified: Optional[bool] = None
    manager_approved: Optional[bool] = False
    user_message: Optional[str] = None
    customer_message: Optional[str] = None


class EvaluateResponse(BaseModel):
    decision: DecisionType
    policy_id: Optional[str] = None
    policy_version: Optional[str] = "v1.0"
    severity: Optional[SeverityType] = None
    risk_level: Optional[str] = None
    reason: str
    safe_response: Optional[str] = None
    modified_arguments: Optional[Dict[str, Any]] = None
    arguments: Optional[Dict[str, Any]] = None
    requires_human_review: bool = False
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    request_id: str
    conversation_id: str
    policy_version: str
    decision: DecisionType
    severity: SeverityType
    policy_id: Optional[str] = None
    reason: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    proposed_action: Optional[ProposedAction] = None
    approved_action: Optional[AuthorizationEnvelope] = None
    safe_response: Optional[str] = None
    modified_arguments: Optional[Dict[str, Any]] = None
    requires_human_review: bool = False
    tool_executed: bool = False
    tool_result: Optional[Dict[str, Any]] = None
    final_response: str
    agent_a_response: Optional[str] = None
    original_response: Optional[str] = None
    corrected_response: Optional[str] = None
    remediation_type: Optional[str] = None
    agent_b_called: bool = False
    incident_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
