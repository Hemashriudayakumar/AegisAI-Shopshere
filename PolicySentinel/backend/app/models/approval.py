import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True, index=True)
    decision_id = Column(String, unique=True, index=True, nullable=False)
    request_id = Column(String, index=True, nullable=False)
    conversation_id = Column(String, index=True, nullable=False)
    policy_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    proposed_action = Column(Text, nullable=False) # JSON-serialized
    status = Column(String, default="PENDING", nullable=False) # PENDING, APPROVED, REJECTED
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
