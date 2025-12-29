from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.reading_service import ReadingService
from app.schemas.reading import (
    SessionStart, SessionOut, ReadingProgressOut, ReadingHistoryOut, HeartbeatIn, SessionEnd
)

router = APIRouter(prefix="/reading", tags=["Reading"])


@router.post("/session/start", response_model=SessionOut)
async def start_session(
    data: SessionStart,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Start a new reading session."""
    service = ReadingService(db)
    try:
        return await service.start_session(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/session/{session_id}/pause", response_model=SessionOut)
async def pause_session(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Pause a reading session."""
    service = ReadingService(db)
    try:
        return await service.pause_session(current_user.id, session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/session/{session_id}/resume", response_model=SessionOut)
async def resume_session(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Resume a paused reading session."""
    service = ReadingService(db)
    try:
        return await service.resume_session(current_user.id, session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/session/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    data: SessionEnd | None = None
):
    """End a reading session."""
    service = ReadingService(db)
    final_delta = data.final_delta_seconds if data else 0
    try:
        return await service.end_session(current_user.id, session_id, final_delta)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/session/{session_id}/heartbeat", response_model=SessionOut)
async def heartbeat_session(
    session_id: int,
    data: HeartbeatIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Send heartbeat to update active duration."""
    service = ReadingService(db)
    try:
        return await service.heartbeat_session(current_user.id, session_id, data.delta_seconds)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/progress/{pdf_id}", response_model=ReadingProgressOut)
async def get_reading_progress(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get reading progress for a PDF."""
    service = ReadingService(db)
    try:
        return await service.get_reading_progress(current_user.id, pdf_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/history/{pdf_id}", response_model=ReadingHistoryOut)
async def get_reading_history(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get reading history for a PDF."""
    service = ReadingService(db)
    try:
        return await service.get_reading_history(current_user.id, pdf_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
