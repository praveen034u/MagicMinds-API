"""Game sessions router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from ..deps.auth import get_current_user, CurrentUser
from ..deps.db import get_db, set_rls_context
from ..models.game_session import MultiplayerGameSession, MultiplayerGameScore
from ..models.game_room import GameRoom
from ..schemas.session import (
    GameSessionCreate,
    GameSessionResponse,
    GameScoreCreate,
    GameScoreResponse
)

router = APIRouter()

@router.post("", response_model=GameSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_game_session(
    session_data: GameSessionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new game session."""
    await set_rls_context(db, current_user.sub)
    
    # Verify room exists
    result = await db.execute(
        select(GameRoom).where(GameRoom.id == session_data.room_id)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Create session
    session = MultiplayerGameSession(
        room_id=session_data.room_id,
        game_id=session_data.game_id,
        difficulty=session_data.difficulty,
        selected_category=session_data.selected_category
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session

@router.get("/{session_id}", response_model=GameSessionResponse)
async def get_game_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a game session by ID."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(MultiplayerGameSession).where(MultiplayerGameSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session

@router.post("/scores", response_model=GameScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_game_score(
    score_data: GameScoreCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Record a game score."""
    await set_rls_context(db, current_user.sub)
    
    score = MultiplayerGameScore(
        room_id=score_data.room_id,
        session_id=score_data.session_id,
        child_id=score_data.child_id,
        score=score_data.score,
        time_spent=score_data.time_spent,
        questions_answered=score_data.questions_answered,
        correct_answers=score_data.correct_answers
    )
    db.add(score)
    await db.commit()
    await db.refresh(score)
    
    return score

@router.get("/room/{room_id}/scores", response_model=List[GameScoreResponse])
async def get_room_scores(
    room_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all scores for a room."""
    await set_rls_context(db, current_user.sub)
    
    result = await db.execute(
        select(MultiplayerGameScore).where(MultiplayerGameScore.room_id == room_id)
    )
    scores = result.scalars().all()
    
    return scores
