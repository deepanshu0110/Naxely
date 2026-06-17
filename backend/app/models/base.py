from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, func

Base = declarative_base()


class TimestampMixin:
    """Mixin for automatic timestamp columns"""
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)