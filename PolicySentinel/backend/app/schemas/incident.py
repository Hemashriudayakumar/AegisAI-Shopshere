from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class IncidentRead(BaseModel):
    id: str
    request_id: str
    conversation_id: str
    customer_id: str
    customer_message: str
    agent_a_proposal: Optional[Dict[str, Any]] = None
    policy_id: str
    severity: str
    reason: str
    evidence: Optional[Dict[str, Any]] = None
    decision: str
    safe_response: Optional[str] = None
    escalation_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    items: List[IncidentRead]
    total: int
