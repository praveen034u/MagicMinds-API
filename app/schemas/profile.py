"""Profile schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class ParentProfileCreate(BaseModel):
    name: str

class ParentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    auth0_user_id: str
    email: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ChildProfileCreate(BaseModel):
    name: str
    age_group: str = Field(..., description="e.g., '5-7', '8-10', '11-13'")
    avatar: Optional[str] = None

class ChildProfileUpdate(BaseModel):
    name: Optional[str] = None
    age_group: Optional[str] = None
    avatar: Optional[str] = None
    voice_clone_enabled: Optional[bool] = None
    voice_clone_url: Optional[str] = None

class ChildOnlineStatusUpdate(BaseModel):
    is_online: Optional[bool] = None
    in_room: Optional[bool] = None
    room_id: Optional[UUID] = None

class ChildProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    parent_id: UUID
    name: str
    age_group: str
    avatar: Optional[str] = None
    voice_clone_enabled: bool
    voice_clone_url: Optional[str] = None
    is_online: bool
    last_seen_at: datetime
    in_room: bool
    room_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
