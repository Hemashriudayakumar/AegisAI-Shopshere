import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False, default="HIGH")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    versions = relationship("PolicyVersion", back_populates="policy", cascade="all, delete-orphan")


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id = Column(String, primary_key=True, index=True)
    policy_id = Column(String, ForeignKey("policies.policy_id"), nullable=False, index=True)
    version = Column(String, nullable=False)
    definition_yaml = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    policy = relationship("Policy", back_populates="versions")
