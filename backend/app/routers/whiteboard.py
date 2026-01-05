"""
Collaborative Whiteboard API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.whiteboard import WhiteboardPermission
from app.services.whiteboard_service import WhiteboardService


router = APIRouter(prefix="/whiteboard", tags=["Collaborative Whiteboard"])


# ============== Schemas ==============

class SessionCreate(BaseModel):
    title: str
    description: str | None = None
    course_id: int | None = None
    subject_code: str | None = None
    topic: str | None = None
    enable_voice: bool = False


class InviteRequest(BaseModel):
    user_id: int
    permission: str = "DRAW"  # VIEW, DRAW, EXPLAIN


class SnapshotCreate(BaseModel):
    canvas_data: dict
    name: str | None = None


class CloseRequest(BaseModel):
    final_canvas: dict | None = None


class SessionResponse(BaseModel):
    id: int
    title: str
    description: str | None
    course_id: int | None
    subject_code: str | None
    topic: str | None
    status: str
    is_readonly: bool
    voice_room_url: str | None
    created_at: datetime
    closed_at: datetime | None
    
    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    permission: str
    draw_color: str | None
    joined_at: datetime
    
    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    id: int
    session_id: int
    name: str | None
    canvas_data: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Session Management ==============

@router.post("", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new whiteboard session."""
    service = WhiteboardService(db)
    session = await service.create_session(
        created_by=current_user.id,
        **data.model_dump()
    )
    return session


@router.get("/active", response_model=list[SessionResponse])
async def get_active_sessions(
    course_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active whiteboard sessions the user is part of."""
    service = WhiteboardService(db)
    sessions = await service.get_active_sessions(
        course_id=course_id,
        user_id=current_user.id
    )
    return sessions


@router.get("/closed", response_model=list[SessionResponse])
async def get_closed_sessions(
    course_id: int | None = None,
    topic: str | None = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get closed sessions for revision."""
    service = WhiteboardService(db)
    sessions = await service.get_closed_sessions(
        course_id=course_id,
        topic=topic,
        limit=limit
    )
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session details."""
    service = WhiteboardService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.get("/{session_id}/canvas")
async def get_canvas(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current canvas data."""
    service = WhiteboardService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"canvas_data": session.canvas_data}


@router.post("/{session_id}/close")
async def close_session(
    session_id: int,
    data: CloseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Close a whiteboard session."""
    service = WhiteboardService(db)
    
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Only creator or admin can close
    if session.created_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only session creator can close"
        )
    
    session = await service.close_session(session_id, data.final_canvas)
    return {"message": "Session closed"}


# ============== Participant Management ==============

@router.post("/{session_id}/invite", response_model=ParticipantResponse)
async def invite_participant(
    session_id: int,
    data: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a user to the whiteboard."""
    service = WhiteboardService(db)
    
    permission = WhiteboardPermission.DRAW
    if data.permission == "VIEW":
        permission = WhiteboardPermission.VIEW
    elif data.permission == "EXPLAIN":
        permission = WhiteboardPermission.EXPLAIN
    
    participant = await service.invite_participant(
        session_id=session_id,
        user_id=data.user_id,
        permission=permission,
        invited_by=current_user.id
    )
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot invite to this session"
        )
    
    return participant


@router.get("/{session_id}/participants", response_model=list[ParticipantResponse])
async def get_participants(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all participants in a session."""
    service = WhiteboardService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session.participants


@router.put("/{session_id}/participants/{user_id}/permission")
async def update_permission(
    session_id: int,
    user_id: int,
    permission: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a participant's permission."""
    service = WhiteboardService(db)
    
    perm = WhiteboardPermission.DRAW
    if permission == "VIEW":
        perm = WhiteboardPermission.VIEW
    elif permission == "EXPLAIN":
        perm = WhiteboardPermission.EXPLAIN
    
    participant = await service.update_permission(session_id, user_id, perm)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )
    
    return {"message": "Permission updated"}


@router.get("/{session_id}/can-draw")
async def check_can_draw(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if current user can draw on the whiteboard."""
    service = WhiteboardService(db)
    can_draw = await service.can_draw(session_id, current_user.id)
    return {"can_draw": can_draw}


# ============== Snapshot Management ==============

@router.post("/{session_id}/snapshots", response_model=SnapshotResponse)
async def save_snapshot(
    session_id: int,
    data: SnapshotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save a snapshot of the current whiteboard state."""
    service = WhiteboardService(db)
    snapshot = await service.save_snapshot(
        session_id=session_id,
        canvas_data=data.canvas_data,
        name=data.name,
        created_by=current_user.id
    )
    return snapshot


@router.get("/{session_id}/snapshots", response_model=list[SnapshotResponse])
async def get_snapshots(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all snapshots for a session."""
    service = WhiteboardService(db)
    snapshots = await service.get_snapshots(session_id)
    return snapshots


@router.get("/{session_id}/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    session_id: int,
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific snapshot."""
    service = WhiteboardService(db)
    snapshot = await service.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found"
        )
    return snapshot
