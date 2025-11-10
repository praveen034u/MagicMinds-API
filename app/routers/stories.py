"""Generated stories router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from ..deps.auth import get_current_user, CurrentUser
from ..deps.db import get_db, set_rls_context
from ..models.parent_profile import ParentProfile
from ..models.child_profile import ChildProfile
from ..models.generated_story import GeneratedStory
from ..schemas.story import (
    GeneratedStoryCreate,
    GeneratedStoryResponse
)

router = APIRouter()

@router.post("", response_model=GeneratedStoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    story_data: GeneratedStoryCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new generated story."""
    await set_rls_context(db, current_user.sub)
    
    # Verify child exists
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == story_data.child_id)
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Create story
    story = GeneratedStory(
        child_id=story_data.child_id,
        story_text=story_data.story_text,
        prompt_used=story_data.prompt_used,
        voice_audio_url=story_data.voice_audio_url
    )
    db.add(story)
    await db.commit()
    await db.refresh(story)
    
    return story

@router.get("", response_model=List[GeneratedStoryResponse])
async def get_stories(
    child_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all stories for a child."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(GeneratedStory).where(GeneratedStory.child_id == child_id)
    )
    stories = result.scalars().all()
    
    return stories

@router.get("/{story_id}", response_model=GeneratedStoryResponse)
async def get_story(
    story_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific story."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(GeneratedStory).where(GeneratedStory.id == story_id)
    )
    story = result.scalar_one_or_none()
    
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    
    return story

@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a story."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(GeneratedStory).where(GeneratedStory.id == story_id)
    )
    story = result.scalar_one_or_none()
    
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    
    await db.delete(story)
    await db.commit()
