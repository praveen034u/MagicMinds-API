"""Game room and participants models."""
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from ..deps.db import Base

class GameRoom(Base):
    """Multiplayer game room."""
    __tablename__ = "game_rooms"
    __table_args__ = (
        CheckConstraint("status IN ('waiting', 'playing', 'finished')", name="ck_game_rooms_status"),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    room_code = Column(String, unique=True, nullable=False, index=True)
    host_child_id = Column(UUID(as_uuid=True), ForeignKey("public.children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    game_id = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    max_players = Column(Integer, nullable=False, default=4)
    current_players = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="waiting")
    has_ai_player = Column(Boolean, nullable=False, default=False)
    ai_player_name = Column(String)
    ai_player_avatar = Column(String)
    selected_category = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    host = relationship("ChildProfile", foreign_keys=[host_child_id], back_populates="hosted_rooms")
    participants = relationship("RoomParticipant", back_populates="room", cascade="all, delete-orphan")
    game_session = relationship("MultiplayerGameSession", back_populates="room", uselist=False)
    scores = relationship("MultiplayerGameScore", back_populates="room", cascade="all, delete-orphan")

class RoomParticipant(Base):
    """Participant in a game room."""
    __tablename__ = "room_participants"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("public.game_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("public.children_profiles.id", ondelete="CASCADE"), index=True)
    player_name = Column(String, nullable=False)
    player_avatar = Column(String)
    is_ai = Column(Boolean, nullable=False, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    
    # Relationships
    room = relationship("GameRoom", back_populates="participants")
