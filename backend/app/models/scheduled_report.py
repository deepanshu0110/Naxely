from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class ScheduledReport(Base):
    __tablename__ = 'scheduled_reports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('templates.id', ondelete='SET NULL'))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='SET NULL'))
    
    name = Column(String(255), nullable=False)
    frequency = Column(String(20), nullable=False)
    next_run_at = Column(DateTime(timezone=True), nullable=False)
    last_run_at = Column(DateTime(timezone=True))
    
    # Data source
    sheets_url = Column(Text)
    csv_storage_path = Column(Text)
    
    # Snapshot of report config (sections, column_config, brand, etc.)
    config_json = Column(Text)
    
    # Email recipients
    recipient_emails = Column(ARRAY(Text), nullable=False)  # type: ignore[var-annotated]
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='scheduled_reports')
    template = relationship('Template', back_populates='scheduled_reports')
    workspace = relationship('Workspace', back_populates='scheduled_reports')