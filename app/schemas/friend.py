"""Friend schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class FriendRequestCreate(BaseModel):
    addressee_id: UUID

class FriendRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    requester_id: UUID
    addressee_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

class FriendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    requester_id: UUID
    addressee_id: UUID
    status: str
    created_at: datetime
