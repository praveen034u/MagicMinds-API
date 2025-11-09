"""Generated story model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..deps.db import Base

class GeneratedStory(Base):
    """AI-generated story for a child."""
    __tablename__ = "generated_stories"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    child_id = Column(UUID(as_uuid=True), ForeignKey("public.children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    audio_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    
    # Relationships
    child = relationship("ChildProfile", back_populates="generated_stories")
