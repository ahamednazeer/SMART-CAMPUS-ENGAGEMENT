"""
Live Doubt Session API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.doubt_session_service import DoubtSessionService


router = APIRouter(prefix="/doubt-sessions", tags=["Doubt Sessions"])


# ============== Schemas ==============

class SessionCreate(BaseModel):
    title: str
    description: str | None = None
    course_id: int | None = None
    subject_code: str | None = None
    scheduled_at: datetime
    duration_minutes: int = 60
    max_participants: int = 50


class QuestionCreate(BaseModel):
    question_text: str


class SummaryCreate(BaseModel):
    summary_text: str
    key_topics: str | None = None


class SessionResponse(BaseModel):
    id: int
    faculty_id: int
    title: str
    description: str | None
    course_id: int | None
    subject_code: str | None
    scheduled_at: datetime
    duration_minutes: int
    max_participants: int
    status: str
    room_url: str | None
    
    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    question_text: str
    status: str
    answer_text: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Faculty Endpoints ==============

@router.post("", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new doubt session (Faculty only)."""
    service = DoubtSessionService(db)
    session = await service.create_session(
        faculty_id=current_user.id,
        **data.model_dump()
    )
    return session


@router.get("/my-sessions", response_model=list[SessionResponse])
async def get_my_sessions(
    include_past: bool = False,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Get sessions created by the current faculty."""
    service = DoubtSessionService(db)
    sessions = await service.get_faculty_sessions(current_user.id, include_past)
    return sessions


@router.post("/{session_id}/start")
async def start_session(
    session_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Start a scheduled session."""
    service = DoubtSessionService(db)
    session = await service.start_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start this session"
        )
    return {"message": "Session started", "room_url": session.room_url}


@router.post("/{session_id}/end")
async def end_session(
    session_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """End a live session."""
    service = DoubtSessionService(db)
    session = await service.end_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot end this session"
        )
    return {"message": "Session ended"}


@router.post("/{session_id}/cancel")
async def cancel_session(
    session_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a session."""
    service = DoubtSessionService(db)
    session = await service.cancel_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel this session"
        )
    return {"message": "Session cancelled"}


# ============== Question Management (Faculty) ==============

@router.get("/{session_id}/questions/pending", response_model=list[QuestionResponse])
async def get_pending_questions(
    session_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending questions in a session."""
    service = DoubtSessionService(db)
    questions = await service.get_pending_questions(session_id)
    return questions


@router.post("/{session_id}/questions/{question_id}/accept")
async def accept_question(
    session_id: int,
    question_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Accept a question for answering."""
    service = DoubtSessionService(db)
    question = await service.accept_question(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return {"message": "Question accepted"}


@router.post("/{session_id}/questions/{question_id}/answer")
async def answer_question(
    session_id: int,
    question_id: int,
    answer_text: str | None = None,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Mark a question as answered."""
    service = DoubtSessionService(db)
    question = await service.answer_question(question_id, answer_text)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return {"message": "Question answered"}


@router.post("/{session_id}/questions/{question_id}/skip")
async def skip_question(
    session_id: int,
    question_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Skip a question."""
    service = DoubtSessionService(db)
    question = await service.skip_question(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return {"message": "Question skipped"}


# ============== Summary ==============

@router.post("/{session_id}/summary")
async def add_summary(
    session_id: int,
    data: SummaryCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Add a post-session summary."""
    service = DoubtSessionService(db)
    summary = await service.add_summary(
        session_id=session_id,
        summary_text=data.summary_text,
        key_topics=data.key_topics,
        created_by=current_user.id
    )
    return {"message": "Summary added", "id": summary.id}


@router.get("/{session_id}/summary")
async def get_summary(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session summary."""
    service = DoubtSessionService(db)
    summary = await service.get_summary(session_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )
    return {
        "summary_text": summary.summary_text,
        "key_topics": summary.key_topics,
        "created_at": summary.created_at
    }


# ============== Student Endpoints ==============

@router.get("/upcoming", response_model=list[SessionResponse])
async def get_upcoming_sessions(
    course_id: int | None = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming doubt sessions."""
    service = DoubtSessionService(db)
    sessions = await service.get_upcoming_sessions(course_id=course_id, limit=limit)
    return sessions


@router.get("/live", response_model=list[SessionResponse])
async def get_live_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get currently live sessions."""
    service = DoubtSessionService(db)
    sessions = await service.get_live_sessions()
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session details."""
    service = DoubtSessionService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.post("/{session_id}/join")
async def join_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join a session."""
    service = DoubtSessionService(db)
    participant = await service.join_session(session_id, current_user.id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join this session (full or not available)"
        )
    
    session = await service.get_session(session_id)
    return {
        "message": "Joined session",
        "room_url": session.room_url if session else None
    }


@router.post("/{session_id}/leave")
async def leave_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a session."""
    service = DoubtSessionService(db)
    await service.leave_session(session_id, current_user.id)
    return {"message": "Left session"}


@router.get("/{session_id}/participants/count")
async def get_participant_count(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the number of participants in a session."""
    service = DoubtSessionService(db)
    count = await service.get_participant_count(session_id)
    return {"count": count}


# ============== Student Questions ==============

@router.post("/{session_id}/questions", response_model=QuestionResponse)
async def ask_question(
    session_id: int,
    data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ask a question in a session."""
    service = DoubtSessionService(db)
    question = await service.ask_question(
        session_id=session_id,
        student_id=current_user.id,
        question_text=data.question_text
    )
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ask questions (session not live)"
        )
    return question
