"""Friend relationship model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, text, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from ..deps.db import Base

class Friend(Base):
    """Friend relationship between two children."""
    __tablename__ = "friends"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friends_requester_addressee"),
        CheckConstraint("status IN ('pending', 'accepted', 'blocked')", name="ck_friends_status"),
        {"schema": "public"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    requester_id = Column(UUID(as_uuid=True), ForeignKey("public.children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    addressee_id = Column(UUID(as_uuid=True), ForeignKey("public.children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
