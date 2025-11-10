"""Game session schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class GameSessionCreate(BaseModel):
    room_id: UUID
    game_id: str
    difficulty: str
    selected_category: Optional[str] = None

class GameSessionUpdate(BaseModel):
    game_data: Optional[Dict[str, Any]] = None
    current_turn_player_id: Optional[UUID] = None
    game_state: Optional[str] = None

class GameSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    room_id: UUID
    game_id: str
    difficulty: str
    selected_category: Optional[str] = None
    game_data: Optional[Dict[str, Any]] = None
    current_turn_player_id: Optional[UUID] = None
    game_state: str
    created_at: datetime
    updated_at: datetime

class GameScoreCreate(BaseModel):
    room_id: UUID
    session_id: UUID
    child_id: Optional[UUID] = None
    score: int
    time_spent: Optional[int] = None
    questions_answered: Optional[int] = None
    correct_answers: Optional[int] = None

class GameScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    room_id: UUID
    session_id: UUID
    child_id: Optional[UUID] = None
    score: int
    time_spent: Optional[int] = None
    questions_answered: Optional[int] = None
    correct_answers: Optional[int] = None
    created_at: datetime
