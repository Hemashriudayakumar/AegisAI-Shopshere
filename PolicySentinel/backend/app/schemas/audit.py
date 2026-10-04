from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class AuditEventRead(BaseModel):
    id: str
    request_id: str
    conversation_id: str
    customer_id: str
    customer_message: str
    agent_a_response: Optional[str] = None
    proposed_action: Optional[Dict[str, Any]] = None
    agent_b_action: Optional[Dict[str, Any]] = None
    policy_id: Optional[str] = None
    policy_version: Optional[str] = None
    severity: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    decision: str
    safe_response: Optional[str] = None
    tool_executed: bool = False
    tool_result: Optional[Dict[str, Any]] = None
    escalation_status: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventListResponse(BaseModel):
    items: List[AuditEventRead]
    total: int
