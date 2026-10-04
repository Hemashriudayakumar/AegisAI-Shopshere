import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RefundRecord(BaseModel):
    order_id: str
    amount: float
    timestamp: str

class ConversationContext(BaseModel):
    conversation_id: str
    customer_id: str
    customer_verified: bool = False
    verified_at: Optional[datetime.datetime] = None
    previous_refunds: List[Dict[str, Any]] = Field(default_factory=list)
    complaint_count: int = 0
    order_lookups: Dict[str, Any] = Field(default_factory=dict)
    last_updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    model_config = {
        "from_attributes": True
    }
