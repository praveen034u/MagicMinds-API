"""Pydantic schemas for request/response models."""
from .profile import (
    ParentProfileCreate, ParentProfileResponse,
    ChildProfileCreate, ChildProfileUpdate, ChildProfileResponse,
    ChildOnlineStatusUpdate
)
from .friend import FriendRequestCreate, FriendResponse, FriendRequestResponse
from .room import (
    GameRoomCreate, GameRoomResponse, RoomParticipantResponse,
    JoinRoomRequest, InviteFriendsRequest, HandleJoinRequestRequest,
    JoinRequestCreate, JoinRequestResponse,
    LeaveRoomRequest, CloseRoomRequest, 
    AcceptInvitationRequest, DeclineInvitationRequest
)
from .story import GeneratedStoryCreate, GeneratedStoryResponse
from .session import (
    GameSessionCreate, GameSessionUpdate, GameSessionResponse,
    GameScoreCreate, GameScoreResponse
)

__all__ = [
    "ParentProfileCreate", "ParentProfileResponse",
    "ChildProfileCreate", "ChildProfileUpdate", "ChildProfileResponse",
    "ChildOnlineStatusUpdate",
    "FriendRequestCreate", "FriendResponse", "FriendRequestResponse",
    "GameRoomCreate", "GameRoomResponse", "RoomParticipantResponse",
    "JoinRoomRequest", "InviteFriendsRequest", "HandleJoinRequestRequest",
    "JoinRequestCreate", "JoinRequestResponse",
    "LeaveRoomRequest", "CloseRoomRequest",
    "AcceptInvitationRequest", "DeclineInvitationRequest",
    "GeneratedStoryCreate", "GeneratedStoryResponse",
    "GameSessionCreate", "GameSessionUpdate", "GameSessionResponse",
    "GameScoreCreate", "GameScoreResponse",
]
