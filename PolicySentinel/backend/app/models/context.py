import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.database import Base

class ConversationContextModel(Base):
    __tablename__ = "conversation_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    conversation_id = Column(String, unique=True, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    customer_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    previous_refunds = Column(Text, default="[]", nullable=False)  # JSON string: [{order_id, amount, timestamp}]
    complaint_count = Column(Integer, default=0, nullable=False)
    order_lookups = Column(Text, default="{}", nullable=False)  # JSON string: {order_id: {status, verified_delivery_date}}
    last_updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
