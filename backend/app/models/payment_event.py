from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class PaymentEvent(Base):
    __tablename__ = 'payment_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    
    event_type = Column(String(100), nullable=False)
    dodo_event_id = Column(String(255), unique=True)
    payload = Column(JSONB, nullable=False)
    processed = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationship
    user = relationship('User', back_populates='payment_events')