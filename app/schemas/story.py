"""Story schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class GeneratedStoryCreate(BaseModel):
    title: str
    content: str
    audio_url: Optional[str] = None

class GeneratedStoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    child_id: UUID
    title: str
    content: str
    audio_url: Optional[str] = None
    created_at: datetime
