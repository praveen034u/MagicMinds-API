"""Voice subscription model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from ..deps.db import Base

class VoiceSubscription(Base):
    """Voice cloning subscription for parent."""
    __tablename__ = "voice_subscriptions"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    parent_id = Column(UUID(as_uuid=True), ForeignKey("public.parent_profiles.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    stripe_subscription_id = Column(String)
    stripe_customer_id = Column(String)
    status = Column(String, nullable=False, default="inactive")
    plan_type = Column(String, nullable=False, default="basic")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parent = relationship("ParentProfile", back_populates="voice_subscription")
