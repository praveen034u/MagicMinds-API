"""Child profile model."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from ..deps.db import Base

class ChildProfile(Base):
    """Child profile belonging to a parent."""
    __tablename__ = "children_profiles"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    parent_id = Column(UUID(as_uuid=True), ForeignKey("public.parent_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    age_group = Column(String, nullable=False)
    avatar = Column(String)
    voice_clone_enabled = Column(Boolean, default=False, server_default=text("false"))
    voice_clone_url = Column(String)
    is_online = Column(Boolean, default=False, server_default=text("false"))
    last_seen_at = Column(DateTime(timezone=True), server_default=text("now()"))
    in_room = Column(Boolean, default=False, server_default=text("false"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("public.game_rooms.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parent = relationship("ParentProfile", back_populates="children")
    current_room = relationship("GameRoom", foreign_keys=[room_id])
    hosted_rooms = relationship("GameRoom", foreign_keys="GameRoom.host_child_id", back_populates="host")
    generated_stories = relationship("GeneratedStory", back_populates="child", cascade="all, delete-orphan")
