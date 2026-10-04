import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime
from app.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    conversation_id = Column(String, index=True, nullable=False)
    customer_id = Column(String, index=True, nullable=False)
    customer_message = Column(Text, nullable=False)
    agent_a_response = Column(Text, nullable=True)
    proposed_action = Column(Text, nullable=True)  # JSON-serialized
    agent_b_action = Column(Text, nullable=True)   # JSON-serialized
    policy_id = Column(String, index=True, nullable=True)
    policy_version = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    evidence = Column(Text, nullable=True)         # JSON-serialized
    decision = Column(String, index=True, nullable=False) # ALLOW, MODIFY, BLOCK, ESCALATE
    safe_response = Column(Text, nullable=True)
    tool_executed = Column(Boolean, default=False, nullable=False)
    tool_result = Column(Text, nullable=True)      # JSON-serialized
    escalation_status = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
