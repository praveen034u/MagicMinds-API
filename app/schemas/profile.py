"""Profile schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class ParentProfileCreate(BaseModel):
    """Schema for creating a parent profile. Email and auth0_user_id are automatically extracted from the authentication token."""
    name: str = Field(..., description="Parent's full name", example="John Doe")

class ParentProfileResponse(BaseModel):
    """Complete parent profile with all fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique identifier for the parent profile")
    auth0_user_id: str = Field(..., description="Auth0 user ID from authentication token")
    email: str = Field(..., description="Email address from authentication token")
    name: Optional[str] = Field(None, description="Parent's full name", example="John Doe")
    created_at: datetime = Field(..., description="Timestamp when profile was created")
    updated_at: datetime = Field(..., description="Timestamp when profile was last updated")

class ChildProfileCreate(BaseModel):
    """Schema for creating a child profile."""
    name: str = Field(..., description="Child's name", example="Emma")
    age_group: str = Field(..., description="Age group category", example="5-7")
    avatar: Optional[str] = Field(None, description="Avatar emoji or image URL", example="👧")

class ChildProfileUpdate(BaseModel):
    """Schema for updating a child profile. All fields are optional."""
    name: Optional[str] = Field(None, description="Child's name", example="Emma")
    age_group: Optional[str] = Field(None, description="Age group category", example="8-10")
    avatar: Optional[str] = Field(None, description="Avatar emoji or image URL", example="👧")
    voice_clone_enabled: Optional[bool] = Field(None, description="Whether voice cloning is enabled")
    voice_clone_url: Optional[str] = Field(None, description="URL to the cloned voice file")

class ChildOnlineStatusUpdate(BaseModel):
    """Schema for updating child's online and room status."""
    is_online: Optional[bool] = Field(None, description="Whether the child is currently online")
    in_room: Optional[bool] = Field(None, description="Whether the child is currently in a game room")
    room_id: Optional[UUID] = Field(None, description="ID of the room the child is in")

class ChildProfileResponse(BaseModel):
    """Complete child profile with all fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Unique identifier for the child profile")
    parent_id: UUID = Field(..., description="ID of the parent profile")
    name: str = Field(..., description="Child's name", example="Emma")
    age_group: str = Field(..., description="Age group category", example="5-7")
    avatar: Optional[str] = Field(None, description="Avatar emoji or image URL", example="👧")
    voice_clone_enabled: bool = Field(False, description="Whether voice cloning is enabled")
    voice_clone_url: Optional[str] = Field(None, description="URL to the cloned voice file")
    is_online: bool = Field(False, description="Whether the child is currently online")
    last_seen_at: Optional[datetime] = Field(None, description="Timestamp of last activity")
    in_room: bool = Field(False, description="Whether the child is currently in a game room")
    room_id: Optional[UUID] = Field(None, description="ID of the room the child is in")
    created_at: datetime = Field(..., description="Timestamp when profile was created")
    updated_at: datetime = Field(..., description="Timestamp when profile was last updated")
