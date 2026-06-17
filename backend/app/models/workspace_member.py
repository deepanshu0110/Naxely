from sqlalchemy import Column, String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class WorkspaceMember(Base):
    __tablename__ = 'workspace_members'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), default='member')
    invited_at = Column(DateTime(timezone=True), default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    
    __table_args__ = (UniqueConstraint('workspace_id', 'user_id'),)
    
    # Relationships
    workspace = relationship('Workspace', back_populates='members')
    user = relationship('User', back_populates='workspace_memberships')