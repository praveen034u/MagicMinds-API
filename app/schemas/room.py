"""Game room schemas."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class GameRoomCreate(BaseModel):
    game_id: str
    difficulty: str
    max_players: int = Field(default=4, ge=2, le=8)
    has_ai_player: bool = False
    ai_player_name: Optional[str] = None
    ai_player_avatar: Optional[str] = None
    selected_category: Optional[str] = None

class RoomParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    room_id: UUID
    child_id: Optional[UUID] = None
    player_name: str
    player_avatar: Optional[str] = None
    is_ai: bool
    joined_at: datetime

class GameRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    room_code: str
    host_child_id: UUID
    game_id: str
    difficulty: str
    max_players: int
    current_players: int
    status: str
    has_ai_player: bool
    ai_player_name: Optional[str] = None
    ai_player_avatar: Optional[str] = None
    selected_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    participants: Optional[List[RoomParticipantResponse]] = None

class JoinRoomRequest(BaseModel):
    room_code: str
    child_id: UUID

class InviteFriendsRequest(BaseModel):
    friend_ids: List[UUID]

class HandleJoinRequestRequest(BaseModel):
    approve: bool
