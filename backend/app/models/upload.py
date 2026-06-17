from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Upload(Base):
    __tablename__ = 'uploads'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # File info
    filename = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    file_size_bytes = Column(Integer)
    source_type = Column(String(20), default='csv')
    
    # Parsed metadata
    row_count = Column(Integer)
    column_count = Column(Integer)
    columns_meta = Column(JSONB, default=list)
    
    # Lifecycle
    expires_at = Column(DateTime(timezone=True), server_default=text("NOW() + interval '24 hours'"))
    used = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationship
    user = relationship('User', back_populates='uploads')