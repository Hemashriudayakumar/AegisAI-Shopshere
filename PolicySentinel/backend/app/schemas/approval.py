from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict

class ApprovalActionRequest(BaseModel):
    reviewer_notes: Optional[str] = None


class ApprovalRead(BaseModel):
    id: str
    decision_id: str
    request_id: str
    conversation_id: str
    policy_id: str
    action_type: str
    proposed_action: Dict[str, Any]
    status: str
    reviewer_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
