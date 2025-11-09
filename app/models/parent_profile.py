"""Parent profile model."""
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from ..deps.db import Base

class ParentProfile(Base):
    """Parent profile linked to Auth0 user."""
    __tablename__ = "parent_profiles"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    auth0_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    children = relationship("ChildProfile", back_populates="parent", cascade="all, delete-orphan")
    voice_subscription = relationship("VoiceSubscription", back_populates="parent", uselist=False)
