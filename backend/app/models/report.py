from sqlalchemy import Column, String, DateTime, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    __tablename__ = 'reports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='SET NULL'))
    
    # Report Identity
    title = Column(String(255), nullable=False)
    template_type = Column(String(50), default='marketing')
    status = Column(String(20), default='pending')
    
    # Input Data
    source_type = Column(String(20), default='csv')
    source_url = Column(Text)
    source_filename = Column(String(255))
    row_count = Column(Integer)
    column_count = Column(Integer)
    
    # Report Config
    config = Column(JSONB, default=dict)
    
    # Output
    pdf_url = Column(Text)
    ppt_url = Column(Text)
    share_token = Column(String(64))
    share_expires_at = Column(DateTime(timezone=True))
    share_view_count = Column(Integer, default=0)
    
    # AI Content
    ai_summary = Column(Text)
    ai_insights = Column(JSONB, default=list)
    ai_anomalies = Column(JSONB, default=list)
    
    # Performance
    generation_time_seconds = Column(Float)
    current_step = Column(String(50))
    error_message = Column(Text)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship('User', back_populates='reports')
    workspace = relationship('Workspace', back_populates='reports')