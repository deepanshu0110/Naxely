from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Workspace(Base, TimestampMixin):
    __tablename__ = 'workspaces'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    name = Column(String(255), nullable=False)
    client_name = Column(String(255))
    logo_url = Column(Text)
    brand_color = Column(String(7))
    
    # Relationships
    owner = relationship('User', back_populates='workspaces_owned')
    members = relationship('WorkspaceMember', back_populates='workspace')
    reports = relationship('Report', back_populates='workspace')
    scheduled_reports = relationship('ScheduledReport', back_populates='workspace')