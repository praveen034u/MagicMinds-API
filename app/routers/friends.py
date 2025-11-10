"""Friends router for friend request and friend management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, not_, func
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from ..deps.auth import get_current_user, CurrentUser
from ..deps.db import get_db, set_rls_context
from ..models.parent_profile import ParentProfile
from ..models.child_profile import ChildProfile
from ..models.friend import Friend
from ..schemas.friend import (
    FriendRequestCreate,
    FriendRequestResponse,
    FriendResponse
)
from ..schemas.profile import ChildProfileResponse

router = APIRouter()

class FriendWithStatus(BaseModel):
    """Friend profile with online/in-game status."""
    id: UUID
    name: str
    avatar: Optional[str] = None
    age_group: Optional[str] = None
    is_online: bool = False
    status: str  # "online", "offline", "in-game"
    
    class Config:
        from_attributes = True


@router.post("/requests", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a friend request from one child to another."""
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
    
    # Note: In a real implementation, you'd need to pass requester_id in the request
    # For now, we'll assume the first child of the parent is the requester
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.parent_id == parent.id).limit(1)
    )
    requester = result.scalar_one_or_none()
    
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No child profiles found"
        )
    
    # Check if addressee exists
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == request_data.addressee_id)
    )
    addressee = result.scalar_one_or_none()
    
    if not addressee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Addressee child not found"
        )
    
    # Check if friendship already exists
    result = await db.execute(
        select(Friend).where(
            or_(
                and_(Friend.requester_id == requester.id, Friend.addressee_id == request_data.addressee_id),
                and_(Friend.requester_id == request_data.addressee_id, Friend.addressee_id == requester.id)
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already exists"
        )
    
    # Create friend request
    friend_request = Friend(
        requester_id=requester.id,
        addressee_id=request_data.addressee_id,
        status="pending"
    )
    db.add(friend_request)
    await db.commit()
    await db.refresh(friend_request)
    
    return friend_request

@router.post("/requests/{request_id}/accept", response_model=FriendResponse)
async def accept_friend_request(
    request_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a friend request."""
    await set_rls_context(db, current_user.sub)
    
    # Get friend request
    result = await db.execute(
        select(Friend).where(Friend.id == request_id)
    )
    friend_request = result.scalar_one_or_none()
    
    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )
    
    if friend_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request is not pending"
        )
    
    # Update status
    friend_request.status = "accepted"
    await db.commit()
    await db.refresh(friend_request)
    
    return friend_request

@router.post("/requests/{request_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline_friend_request(
    request_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Decline a friend request."""
    await set_rls_context(db, current_user.sub)
    
    # Get friend request
    result = await db.execute(
        select(Friend).where(Friend.id == request_id)
    )
    friend_request = result.scalar_one_or_none()
    
    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found"
        )
    
    # Delete the request
    await db.delete(friend_request)
    await db.commit()

@router.get("", response_model=List[FriendWithStatus])
async def list_friends(
    child_id: UUID = Query(..., description="Child ID to get friends for"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all accepted friends for a child with their online/in-game status."""
    await set_rls_context(db, current_user.sub)
    
    # Get all accepted friendships and join with child profiles
    # Return the friend's profile (not the friendship record)
    result = await db.execute(
        select(ChildProfile).join(
            Friend,
            or_(
                and_(Friend.requester_id == child_id, Friend.addressee_id == ChildProfile.id),
                and_(Friend.addressee_id == child_id, Friend.requester_id == ChildProfile.id)
            )
        ).where(Friend.status == "accepted")
    )
    friend_profiles = result.scalars().all()
    
    # Transform to include status based on room_id
    friends_with_status = []
    for friend in friend_profiles:
        status_str = "offline"
        if friend.is_online:
            status_str = "in-game" if friend.room_id else "online"
        
        friends_with_status.append(FriendWithStatus(
            id=friend.id,
            name=friend.name,
            avatar=friend.avatar,
            age_group=friend.age_group,
            is_online=friend.is_online,
            status=status_str
        ))
    
    return friends_with_status

@router.get("/requests", response_model=List[FriendRequestResponse])
async def get_friend_requests(
    child_id: UUID = Query(..., description="Child ID to get requests for"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending friend requests for a child."""
    await set_rls_context(db, current_user.sub)
    
    # Get pending friend requests where child is the addressee
    result = await db.execute(
        select(Friend).where(
            and_(
                Friend.addressee_id == child_id,
                Friend.status == "pending"
            )
        )
    )
    requests = result.scalars().all()
    
    return requests

@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfriend(
    child_id: UUID,
    friend_child_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a friend relationship."""
    await set_rls_context(db, current_user.sub)
    
    # Find the friendship
    result = await db.execute(
        select(Friend).where(
            or_(
                and_(Friend.requester_id == child_id, Friend.addressee_id == friend_child_id),
                and_(Friend.requester_id == friend_child_id, Friend.addressee_id == child_id)
            )
        )
    )
    friendship = result.scalar_one_or_none()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friendship not found"
        )
    
    await db.delete(friendship)
    await db.commit()

@router.get("/children/search", response_model=List[ChildProfileResponse])
async def search_children(
    q: str = Query(..., description="Search query for child names"),
    child_id: UUID = Query(None, description="Current child ID to exclude from results"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search for children by name, excluding current child and existing friends."""
    await set_rls_context(db, current_user.sub)
    
    # Build base query
    query = select(ChildProfile).where(
        ChildProfile.name.ilike(f"%{q}%")
    )
    
    # Exclude current child if provided
    if child_id:
        query = query.where(ChildProfile.id != child_id)
        
        # Exclude existing friends (both accepted and pending)
        # Subquery to get all friend IDs
        friends_subquery = select(
            func.coalesce(
                Friend.addressee_id,
                Friend.requester_id
            ).label('friend_id')
        ).where(
            or_(
                Friend.requester_id == child_id,
                Friend.addressee_id == child_id
            )
        ).subquery()
        
        query = query.where(not_(ChildProfile.id.in_(select(friends_subquery.c.friend_id))))
    
    result = await db.execute(query.limit(20))
    children = result.scalars().all()
    
    return children

@router.get("/children/all", response_model=List[ChildProfileResponse])
async def list_all_children(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all children profiles (for admin/testing purposes)."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(ChildProfile).order_by(ChildProfile.created_at.desc()).limit(100)
    )
    children = result.scalars().all()
    
    return children
