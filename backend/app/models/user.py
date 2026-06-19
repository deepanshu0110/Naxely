from sqlalchemy import Column, String, DateTime, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(Text)
    auth_provider = Column(String(50), default='email')
    
    # Subscription
    tier = Column(String(20), default='free')
    tier_expires_at = Column(DateTime(timezone=True))
    dodo_customer_id = Column(String(255))
    dodo_subscription_id = Column(String(255))
    
    # AI Settings (encrypted)
    ai_provider = Column(String(20))
    encrypted_api_key = Column(Text)
    api_key_iv = Column(Text)
    api_key_preview = Column(String(20))
    
    # Branding (Pro+)
    logo_url = Column(Text)
    brand_color = Column(String(7), default='#6366F1')
    company_name = Column(String(255))
    
    # Usage Tracking
    reports_this_month = Column(Integer, default=0)
    usage_reset_at = Column(DateTime(timezone=True), server_default=text("date_trunc('month', NOW() + interval '1 month')"))
    
    # Preferences
    theme_preference = Column(String(10), default='light')

    # Soft delete
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    uploads = relationship('Upload', back_populates='user')
    reports = relationship('Report', back_populates='user')
    templates = relationship('Template', back_populates='user')
    workspaces_owned = relationship('Workspace', back_populates='owner')
    workspace_memberships = relationship('WorkspaceMember', back_populates='user')
    payment_events = relationship('PaymentEvent', back_populates='user')
    scheduled_reports = relationship('ScheduledReport', back_populates='user')