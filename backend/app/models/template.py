from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Template(Base, TimestampMixin):
    __tablename__ = 'templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), default='marketing')
    config = Column(JSONB, nullable=False, default=dict)
    is_default = Column(Boolean, default=False)
    
    # Relationships
    user = relationship('User', back_populates='templates')
    scheduled_reports = relationship('ScheduledReport', back_populates='template')