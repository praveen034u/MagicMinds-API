"""Story schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class GeneratedStoryCreate(BaseModel):
    child_id: UUID
    story_text: str
    prompt_used: Optional[str] = None
    voice_audio_url: Optional[str] = None

class GeneratedStoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    child_id: UUID
    story_text: str
    prompt_used: Optional[str] = None
    voice_audio_url: Optional[str] = None
    created_at: datetime

class VoiceSubscriptionCreate(BaseModel):
    stripe_subscription_id: str
    status: str
    plan_type: str

class VoiceSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    parent_id: UUID
    stripe_subscription_id: str
    status: str
    plan_type: str
    created_at: datetime
    updated_at: datetime
