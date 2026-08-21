from sqlalchemy import Column, String, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from .base import Base


class EmailLog(Base):
    __tablename__ = 'email_log'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    email_type = Column(String(50), nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    resend_id = Column(String(255))
    status = Column(String(20), default='sent')

    # relationship is optional — email_log is append-only, no backref needed
