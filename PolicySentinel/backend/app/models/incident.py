import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    conversation_id = Column(String, index=True, nullable=False)
    customer_id = Column(String, index=True, nullable=False)
    customer_message = Column(Text, nullable=False)
    agent_a_proposal = Column(Text, nullable=True) # JSON-serialized
    policy_id = Column(String, index=True, nullable=False)
    severity = Column(String, nullable=False)      # LOW, MEDIUM, HIGH, CRITICAL
    reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)         # JSON-serialized
    decision = Column(String, nullable=False)      # BLOCK, ESCALATE, MODIFY
    safe_response = Column(Text, nullable=True)
    escalation_status = Column(String, default="PENDING", nullable=False) # PENDING, APPROVED, REJECTED, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
