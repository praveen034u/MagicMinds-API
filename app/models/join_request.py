"""Join request model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from ..deps.db import Base

class JoinRequest(Base):
    """Request to join a game room."""
    __tablename__ = "join_requests"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'denied')", name="ck_join_requests_status"),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    room_code = Column(String, nullable=False, index=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("public.children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    player_name = Column(String, nullable=False)
    player_avatar = Column(String)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
