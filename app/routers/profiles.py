"""Profiles router for parent and child profile management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from ..deps.auth import get_current_user, CurrentUser
from ..deps.db import get_db, set_rls_context
from ..models.parent_profile import ParentProfile
from ..models.child_profile import ChildProfile
from ..schemas.profile import (
    ParentProfileCreate,
    ParentProfileResponse,
    ChildProfileCreate,
    ChildProfileUpdate,
    ChildOnlineStatusUpdate,
    ChildProfileResponse
)

router = APIRouter()

@router.get("/test")
async def test_profiles_router():
    """Test endpoint to verify the profiles router is working (no auth required)."""
    return {
        "status": "ok",
        "router": "profiles",
        "message": "Profiles router is working. Use authenticated endpoints with Bearer token."
    }

@router.post("/parent", response_model=ParentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_parent_profile(
    profile_data: ParentProfileCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a parent profile.
    
    **Request Body:**
    - **name**: Parent's full name (required)
    
    **Auto-Extracted from JWT Token (Authorization header):**
    - **auth0_user_id**: Extracted from token's 'sub' claim
    - **email**: Extracted from token's 'email' claim
    
    **Authentication:**
    Include your Auth0 JWT token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    The API automatically:
    1. Verifies the JWT signature using Auth0's public keys
    2. Validates token claims (expiration, audience, issuer)
    3. Extracts user_id from 'sub' claim
    4. Extracts email from 'email' claim
    
    **Behavior:**
    - Returns existing profile if already created (idempotent operation)
    - Creates new profile if none exists for this Auth0 user
    
    See AUTHENTICATION_FLOW.md for detailed authentication documentation.
    """
    await set_rls_context(db, current_user.sub)
    
    # Check if profile already exists - return it instead of erroring (matches edge function)
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    
    # Extract email - use from token if available, otherwise use a placeholder
    email = current_user.email or f"{current_user.sub}@auth0.user"
    
    # Create new profile
    parent = ParentProfile(
        auth0_user_id=current_user.sub,
        email=email,
        name=profile_data.name
    )
    db.add(parent)
    await db.commit()
    await db.refresh(parent)
    
    return parent

@router.get("/parent", response_model=ParentProfileResponse)
async def get_parent_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's parent profile."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    return parent

@router.post("/children", response_model=ChildProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_child_profile(
    child_data: ChildProfileCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a child profile.
    
    - **name**: Child's name (required)
    - **age_group**: Age category like '5-7', '8-10', '11-13' (required)
    - **avatar**: Emoji or image URL (optional)
    
    All other fields (voice_clone_enabled, is_online, in_room, etc.) are automatically initialized.
    """
    await set_rls_context(db, current_user.sub)
    
    # Get parent profile
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found. Create a parent profile first."
        )
    
    # Create child profile
    child = ChildProfile(
        parent_id=parent.id,
        name=child_data.name,
        age_group=child_data.age_group,
        avatar=child_data.avatar
    )
    db.add(child)
    await db.commit()
    await db.refresh(child)
    
    return child

@router.get("/children", response_model=List[ChildProfileResponse])
async def get_children_profiles(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all children profiles for the current parent."""
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
    
    # Get children
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.parent_id == parent.id)
    )
    children = result.scalars().all()
    
    return children

@router.patch("/children/{child_id}", response_model=ChildProfileResponse)
async def update_child_profile(
    child_id: UUID,
    child_data: ChildProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a child profile."""
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
    
    # Get child profile
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.parent_id == parent.id
        )
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found"
        )
    
    # Update fields
    update_data = child_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)
    
    await db.commit()
    await db.refresh(child)
    
    return child

@router.delete("/children/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child_profile(
    child_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a child profile."""
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
    
    # Get child profile
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.parent_id == parent.id
        )
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found"
        )
    
    await db.delete(child)
    await db.commit()

@router.post("/children/{child_id}/status", response_model=ChildProfileResponse)
async def update_child_status(
    child_id: UUID,
    status_data: ChildOnlineStatusUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update child online status and room status. Updates last_seen_at timestamp."""
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
    
    # Get child profile
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.parent_id == parent.id
        )
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child profile not found"
        )
    
    # Update status fields
    update_data = status_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)
    
    # Update last_seen_at timestamp (matches edge function behavior)
    child.last_seen_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(child)
    
    return child
