"""Game session and scores models."""
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from ..deps.db import Base

class MultiplayerGameSession(Base):
    """Multiplayer game session tracking."""
    __tablename__ = "multiplayer_game_sessions"
    __table_args__ = (
        CheckConstraint("game_state IN ('active', 'paused', 'finished')", name="ck_multiplayer_game_sessions_game_state"),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("public.game_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    game_data = Column(JSONB)
    current_turn_player_id = Column(UUID(as_uuid=True))
    game_state = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    room = relationship("GameRoom", back_populates="game_session")

class MultiplayerGameScore(Base):
    """Player scores in multiplayer games."""
    __tablename__ = "multiplayer_game_scores"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("public.game_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("public.children_profiles.id", ondelete="CASCADE"), index=True)
    player_name = Column(String, nullable=False)
    player_avatar = Column(String)
    is_ai = Column(Boolean, nullable=False, default=False)
    score = Column(Integer, nullable=False, default=0)
    total_questions = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    room = relationship("GameRoom", back_populates="scores")
