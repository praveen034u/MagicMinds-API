"""Voice cloning router for ElevenLabs integration."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
import os
import base64
import httpx

from ..deps.auth import get_current_user, CurrentUser
from ..deps.db import get_db, set_rls_context
from ..models.parent_profile import ParentProfile
from ..models.child_profile import ChildProfile
from ..models.voice_subscription import VoiceSubscription

router = APIRouter()

class VoiceCloneRequest(BaseModel):
    """Request to create voice clone."""
    child_id: str
    audio_data: str  # Base64 encoded audio
    file_name: Optional[str] = "voice_sample.wav"

class VoiceCloneResponse(BaseModel):
    """Response from voice clone creation."""
    success: bool
    voice_id: str
    data: Optional[dict] = None

class StoryAudioRequest(BaseModel):
    """Request to generate story audio."""
    story_text: str
    voice_id: str

class StoryAudioResponse(BaseModel):
    """Response with generated audio."""
    success: bool
    audio_content: str  # Base64 encoded audio

@router.post("/create-voice-clone", response_model=VoiceCloneResponse)
async def create_voice_clone(
    voice_data: VoiceCloneRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a voice clone using ElevenLabs API."""
    await set_rls_context(db, current_user.sub)
    
    # Get parent profile
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    # Check if user has active subscription
    result = await db.execute(
        select(VoiceSubscription).where(
            VoiceSubscription.parent_id == parent.id,
            VoiceSubscription.status == "active"
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required for voice cloning"
        )
    
    # Get child profile
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == voice_data.child_id)
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found"
        )
    
    # Check ElevenLabs API key
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ElevenLabs API key not configured"
        )
    
    try:
        # Convert base64 audio to binary
        audio_bytes = base64.b64decode(voice_data.audio_data)
        
        # Create voice clone with ElevenLabs
        async with httpx.AsyncClient() as client:
            # Prepare multipart form data
            files = {
                'files': (voice_data.file_name, audio_bytes, 'audio/wav')
            }
            data = {
                'name': f'Child_{voice_data.child_id}_Voice',
                'description': 'AI cloned voice for storytelling'
            }
            
            response = await client.post(
                'https://api.elevenlabs.io/v1/voices/add',
                headers={'xi-api-key': elevenlabs_api_key},
                files=files,
                data=data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"ElevenLabs API error: {error_text}"
                )
            
            voice_data_response = response.json()
            voice_id = voice_data_response.get('voice_id')
            
            # Update child profile with voice clone info
            child.voice_clone_enabled = True
            child.voice_clone_url = voice_id
            
            await db.commit()
            await db.refresh(child)
            
            return VoiceCloneResponse(
                success=True,
                voice_id=voice_id,
                data={"child_id": str(child.id), "voice_id": voice_id}
            )
    
    except base64.binascii.Error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 audio data"
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with ElevenLabs: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating voice clone: {str(e)}"
        )

@router.post("/generate-story-audio", response_model=StoryAudioResponse)
async def generate_story_audio(
    audio_data: StoryAudioRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate audio from text using ElevenLabs TTS."""
    await set_rls_context(db, current_user.sub)
    
    # Check ElevenLabs API key
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ElevenLabs API key not configured"
        )
    
    try:
        # Generate audio using ElevenLabs TTS
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'https://api.elevenlabs.io/v1/text-to-speech/{audio_data.voice_id}',
                headers={
                    'xi-api-key': elevenlabs_api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'text': audio_data.story_text,
                    'model_id': 'eleven_multilingual_v2',
                    'voice_settings': {
                        'stability': 0.5,
                        'similarity_boost': 0.8
                    }
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"ElevenLabs TTS error: {error_text}"
                )
            
            # Convert audio response to base64
            audio_bytes = response.content
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            
            return StoryAudioResponse(
                success=True,
                audio_content=base64_audio
            )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with ElevenLabs: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating story audio: {str(e)}"
        )
