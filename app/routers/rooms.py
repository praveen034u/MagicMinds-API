"""Game rooms router for room creation and management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
import random
import string

from ..deps.auth import get_current_user, CurrentUser
from ..deps.db import get_db, set_rls_context
from ..models.parent_profile import ParentProfile
from ..models.child_profile import ChildProfile
from ..models.game_room import GameRoom, RoomParticipant
from ..models.join_request import JoinRequest
from ..schemas.room import (
    GameRoomCreate,
    GameRoomResponse,
    RoomParticipantResponse,
    JoinRoomRequest,
    InviteFriendsRequest,
    JoinRequestCreate,
    HandleJoinRequestRequest,
    JoinRequestResponse,
    LeaveRoomRequest,
    CloseRoomRequest,
    AcceptInvitationRequest,
    DeclineInvitationRequest
)

router = APIRouter()

# AI Players configuration (matches edge function)
AI_FRIENDS = [
    {"id": "ai-1", "name": "Alex the Explorer", "avatar": "🧭", "personality": "curious"},
    {"id": "ai-2", "name": "Bella the Builder", "avatar": "🏗️", "personality": "creative"},
    {"id": "ai-3", "name": "Charlie the Chef", "avatar": "👨‍🍳", "personality": "adventurous"},
    {"id": "ai-4", "name": "Diana the Detective", "avatar": "🕵️", "personality": "analytical"}
]

def generate_room_code(length: int = 6) -> str:
    """Generate a random room code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@router.post("", response_model=GameRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: GameRoomCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new game room with optional friend invitations."""
    await set_rls_context(db, current_user.sub)
    
    # Get child from host_child_id in request
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == room_data.host_child_id)
    )
    host_child = result.scalar_one_or_none()
    
    if not host_child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host child not found"
        )
    
    # Check if child is already in another room (matches edge function validation)
    if host_child.room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Child is already in a room"
        )
    
    # Generate unique room code
    room_code = generate_room_code()
    
    # Create room
    room = GameRoom(
        room_code=room_code,
        host_child_id=host_child.id,
        game_id=room_data.game_id,
        difficulty=room_data.difficulty,
        max_players=room_data.max_players,
        current_players=1,
        selected_category=room_data.selected_category
    )
    db.add(room)
    await db.flush()  # Get room.id before adding participants
    
    # Add host as participant
    participant = RoomParticipant(
        room_id=room.id,
        child_id=host_child.id,
        player_name=host_child.name,
        player_avatar=host_child.avatar or '👤',
        is_ai=False
    )
    db.add(participant)
    
    # Auto-add AI player if no friends invited (matches edge function logic)
    friend_ids = getattr(room_data, 'friend_ids', []) or []
    if not friend_ids or len(friend_ids) == 0:
        # Select random AI friend
        ai_friend = random.choice(AI_FRIENDS)
        ai_participant = RoomParticipant(
            room_id=room.id,
            player_name=ai_friend["name"],
            player_avatar=ai_friend["avatar"],
            is_ai=True
        )
        db.add(ai_participant)
        room.current_players += 1
        room.has_ai_player = True
        room.ai_player_name = ai_friend["name"]
        room.ai_player_avatar = ai_friend["avatar"]
    
    # Update child's room status
    host_child.room_id = room.id
    
    await db.commit()
    await db.refresh(room)
    
    # Load participants
    result = await db.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == room.id)
    )
    room.participants = result.scalars().all()
    
    return room

@router.post("/join", response_model=GameRoomResponse)
async def join_room(
    join_data: JoinRoomRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join an existing game room."""
    await set_rls_context(db, current_user.sub)
    
    # Get child
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == join_data.child_id)
    )
    child = result.scalar_one_or_none()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Check if child is already in another room (matches edge function)
    if child.room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already in a room. Leave current room first."
        )
    
    # Get room by code
    result = await db.execute(
        select(GameRoom).where(GameRoom.room_code == join_data.room_code)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    if room.status != "waiting":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is not accepting new players"
        )
    
    if room.current_players >= room.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is full"
        )
    
    # Add participant
    participant = RoomParticipant(
        room_id=room.id,
        child_id=child.id,
        player_name=child.name,
        player_avatar=child.avatar or '👤',
        is_ai=False
    )
    db.add(participant)
    
    # Update room and child
    room.current_players += 1
    child.room_id = room.id
    
    await db.commit()
    await db.refresh(room)
    
    # Load participants
    result = await db.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == room.id)
    )
    room.participants = result.scalars().all()
    
    return room

@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_room(
    leave_data: LeaveRoomRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a game room. If host leaves, room is deleted and all participants are removed."""
    await set_rls_context(db, current_user.sub)
    
    # Get child
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == leave_data.child_id)
    )
    child = result.scalar_one_or_none()
    
    if not child or not child.room_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not in a room"
        )
    
    room_id = child.room_id
    
    # Get room
    result = await db.execute(
        select(GameRoom).where(GameRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    
    if room:
        # If host is leaving, delete the entire room (matches edge function)
        if room.host_child_id == leave_data.child_id:
            # Get all participants and clear their room_id
            result = await db.execute(
                select(RoomParticipant).where(RoomParticipant.room_id == room_id)
            )
            participants = result.scalars().all()
            
            for participant in participants:
                if participant.child_id:
                    result = await db.execute(
                        select(ChildProfile).where(ChildProfile.id == participant.child_id)
                    )
                    participant_child = result.scalar_one_or_none()
                    if participant_child:
                        participant_child.room_id = None
            
            # Delete room (cascade will delete participants)
            await db.delete(room)
        else:
            # Non-host leaving - just remove participant
            result = await db.execute(
                select(RoomParticipant).where(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.child_id == leave_data.child_id
                )
            )
            participant = result.scalar_one_or_none()
            
            if participant:
                await db.delete(participant)
                room.current_players -= 1
            
            # Update child status
            child.room_id = None
    else:
        # Room doesn't exist, just clear child status
        child.room_id = None
    
    await db.commit()

@router.post("/close", status_code=status.HTTP_204_NO_CONTENT)
async def close_room(
    close_data: CloseRoomRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Close a game room (host only). Sets all participants' room_id to null."""
    await set_rls_context(db, current_user.sub)
    
    # Get room
    result = await db.execute(
        select(GameRoom).where(GameRoom.id == close_data.room_id)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Update all participants' status (matches edge function)
    result = await db.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == close_data.room_id)
    )
    participants = result.scalars().all()
    
    participant_ids = [p.child_id for p in participants if p.child_id]
    if participant_ids:
        result = await db.execute(
            select(ChildProfile).where(ChildProfile.id.in_(participant_ids))
        )
        children = result.scalars().all()
        for child in children:
            child.room_id = None
    
    # Delete room (cascade will delete participants)
    await db.delete(room)
    await db.commit()

@router.get("/current", response_model=Optional[GameRoomResponse])
async def get_current_room(
    child_id: UUID = Query(..., description="Child ID to get current room for"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current room for a child. Returns null if not in a room."""
    await set_rls_context(db, current_user.sub)
    
    # Get child's current room_id
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == child_id)
    )
    child = result.scalar_one_or_none()
    
    if not child or not child.room_id:
        return None
    
    # Get room details
    result = await db.execute(
        select(GameRoom).where(GameRoom.id == child.room_id)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        # Room no longer exists, clear the room_id (matches edge function)
        child.room_id = None
        await db.commit()
        return None
    
    # Load participants (matches edge function response structure)
    result = await db.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == room.id)
    )
    room.participants = result.scalars().all()
    
    return room

@router.get("/{room_id}/participants", response_model=List[RoomParticipantResponse])
async def get_room_participants(
    room_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all participants in a room."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == room_id)
    )
    participants = result.scalars().all()
    
    return participants

@router.post("/invite", response_model=dict)
async def invite_friends(
    invite_data: InviteFriendsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite friends to join a game room."""
    await set_rls_context(db, current_user.sub)
    
    # Get room info
    result = await db.execute(
        select(GameRoom).where(GameRoom.room_code == invite_data.room_code)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Get friend profiles for their names and avatars
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id.in_(invite_data.friend_ids))
    )
    friend_profiles = result.scalars().all()
    
    if not friend_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid friends found"
        )
    
    # Create join requests for each friend
    created_invitations = []
    for friend in friend_profiles:
        invitation = JoinRequest(
            room_id=room.id,
            room_code=room.room_code,
            child_id=friend.id,
            player_name=friend.name,
            player_avatar=friend.avatar or '👤',
            status='pending'
        )
        db.add(invitation)
        created_invitations.append(invitation)
    
    await db.commit()
    
    return {
        "success": True,
        "invitations_sent": len(created_invitations),
        "data": created_invitations
    }

@router.post("/request-to-join", response_model=JoinRequestResponse)
async def request_to_join(
    request_data: JoinRequestCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request to join a room by room code."""
    await set_rls_context(db, current_user.sub)
    
    # Check if room exists and is active
    result = await db.execute(
        select(GameRoom).where(GameRoom.room_code == request_data.room_code)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Get requester info
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == request_data.child_id)
    )
    requester = result.scalar_one_or_none()
    
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Create join request
    join_request = JoinRequest(
        room_code=request_data.room_code,
        child_id=request_data.child_id,
        player_name=requester.name,
        player_avatar=requester.avatar or '👤',
        status='pending'
    )
    db.add(join_request)
    await db.commit()
    await db.refresh(join_request)
    
    return join_request

@router.post("/handle-join-request", response_model=dict)
async def handle_join_request(
    handle_data: HandleJoinRequestRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve or deny a join request."""
    await set_rls_context(db, current_user.sub)
    
    # Get the join request
    result = await db.execute(
        select(JoinRequest).where(JoinRequest.id == handle_data.request_id)
    )
    join_request = result.scalar_one_or_none()
    
    if not join_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Update request status
    join_request.status = 'approved' if handle_data.approve else 'denied'
    
    if handle_data.approve:
        # Get room info
        result = await db.execute(
            select(GameRoom).where(GameRoom.room_code == join_request.room_code)
        )
        room = result.scalar_one_or_none()
        
        if room and room.current_players < room.max_players:
            # Get the accepting player's profile
            result = await db.execute(
                select(ChildProfile).where(ChildProfile.id == join_request.child_id)
            )
            accepting_player = result.scalar_one_or_none()
            
            if accepting_player:
                # Add player to room
                participant = RoomParticipant(
                    room_id=room.id,
                    child_id=accepting_player.id,
                    player_name=accepting_player.name,
                    player_avatar=accepting_player.avatar or '👤',
                    is_ai=False
                )
                db.add(participant)
                
                # Set player as in room
                accepting_player.room_id = room.id
                
                # Update room player count
                room.current_players += 1
                
                await db.commit()
                await db.refresh(participant)
                await db.refresh(room)
                
                return {
                    "success": True,
                    "player": participant,
                    "room": room,
                    "room_id": room.id
                }
    
    await db.commit()
    return {"success": True}

@router.get("/pending-invitations", response_model=List[JoinRequestResponse])
async def get_pending_invitations(
    child_id: UUID = Query(..., description="Child ID to get invitations for"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending room invitations for a child."""
    await set_rls_context(db, current_user.sub)
    
    # Query join_requests with room information
    result = await db.execute(
        select(JoinRequest).where(
            JoinRequest.child_id == child_id,
            JoinRequest.status == 'pending'
        ).order_by(JoinRequest.created_at.desc())
    )
    invitations = result.scalars().all()
    
    return invitations

@router.post("/accept-invitation", response_model=dict)
async def accept_invitation(
    accept_data: AcceptInvitationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a room invitation and join the room."""
    await set_rls_context(db, current_user.sub)
    
    # Get the invitation
    result = await db.execute(
        select(JoinRequest).where(
            JoinRequest.id == accept_data.invitation_id,
            JoinRequest.child_id == accept_data.child_id
        )
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    # Update invitation status
    invitation.status = 'approved'
    
    # Get the room
    result = await db.execute(
        select(GameRoom).where(GameRoom.room_code == invitation.room_code)
    )
    room = result.scalar_one_or_none()
    
    if not room or room.current_players >= room.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is full or unavailable"
        )
    
    # Get player info
    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == accept_data.child_id)
    )
    accepting_player = result.scalar_one_or_none()
    
    if not accepting_player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    # Add player to room
    participant = RoomParticipant(
        room_id=room.id,
        child_id=accept_data.child_id,
        player_name=accepting_player.name,
        player_avatar=accepting_player.avatar or '👤',
        is_ai=False
    )
    db.add(participant)
    
    # Set player as in room
    accepting_player.room_id = room.id
    
    # Update room player count
    room.current_players += 1
    
    await db.commit()
    await db.refresh(room)
    
    return {
        "success": True,
        "room": room,
        "room_id": room.id
    }

@router.post("/decline-invitation", response_model=dict)
async def decline_invitation(
    decline_data: DeclineInvitationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Decline a room invitation."""
    await set_rls_context(db, current_user.sub)
    
    # Update invitation status to denied
    result = await db.execute(
        select(JoinRequest).where(
            JoinRequest.id == decline_data.invitation_id,
            JoinRequest.child_id == decline_data.child_id
        )
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    invitation.status = 'denied'
    await db.commit()
    
    return {"success": True}
