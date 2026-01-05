"""
Doubt Session service for live faculty office hours.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doubt_session import (
    DoubtSession, SessionParticipant, SessionQuestion, SessionSummary,
    SessionStatus, QuestionStatus
)


class DoubtSessionService:
    """Service for doubt session management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Session Management ==============
    
    async def create_session(
        self,
        faculty_id: int,
        title: str,
        scheduled_at: datetime,
        duration_minutes: int = 60,
        max_participants: int = 50,
        course_id: int | None = None,
        subject_code: str | None = None,
        description: str | None = None
    ) -> DoubtSession:
        """Create a new doubt session."""
        # Generate a unique room ID for Jitsi
        room_id = f"doubt-{uuid.uuid4().hex[:8]}"
        room_url = f"https://meet.jit.si/{room_id}"
        
        session = DoubtSession(
            faculty_id=faculty_id,
            title=title,
            description=description,
            course_id=course_id,
            subject_code=subject_code,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            max_participants=max_participants,
            room_id=room_id,
            room_url=room_url
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def get_session(self, session_id: int) -> DoubtSession | None:
        """Get a doubt session by ID."""
        result = await self.db.execute(
            select(DoubtSession)
            .options(
                selectinload(DoubtSession.participants),
                selectinload(DoubtSession.questions)
            )
            .where(DoubtSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_upcoming_sessions(
        self,
        course_id: int | None = None,
        faculty_id: int | None = None,
        limit: int = 10
    ) -> list[DoubtSession]:
        """Get upcoming scheduled sessions."""
        now = datetime.utcnow()
        query = select(DoubtSession).where(
            DoubtSession.scheduled_at > now,
            DoubtSession.status == SessionStatus.SCHEDULED
        )
        
        if course_id:
            query = query.where(DoubtSession.course_id == course_id)
        if faculty_id:
            query = query.where(DoubtSession.faculty_id == faculty_id)
        
        query = query.order_by(DoubtSession.scheduled_at).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_faculty_sessions(
        self,
        faculty_id: int,
        include_past: bool = False
    ) -> list[DoubtSession]:
        """Get all sessions for a faculty member."""
        query = select(DoubtSession).where(
            DoubtSession.faculty_id == faculty_id
        )
        
        if not include_past:
            now = datetime.utcnow()
            query = query.where(DoubtSession.scheduled_at >= now - timedelta(hours=2))
        
        query = query.order_by(DoubtSession.scheduled_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_live_sessions(self) -> list[DoubtSession]:
        """Get currently live sessions."""
        result = await self.db.execute(
            select(DoubtSession).where(
                DoubtSession.status == SessionStatus.LIVE
            )
        )
        return list(result.scalars().all())
    
    async def start_session(self, session_id: int) -> DoubtSession | None:
        """Start a scheduled session."""
        session = await self.get_session(session_id)
        if not session or session.status != SessionStatus.SCHEDULED:
            return None
        
        session.status = SessionStatus.LIVE
        session.actual_start_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def end_session(self, session_id: int) -> DoubtSession | None:
        """End a live session."""
        session = await self.get_session(session_id)
        if not session or session.status != SessionStatus.LIVE:
            return None
        
        session.status = SessionStatus.ENDED
        session.actual_end_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def cancel_session(self, session_id: int) -> DoubtSession | None:
        """Cancel a session."""
        session = await self.get_session(session_id)
        if not session or session.status not in [SessionStatus.SCHEDULED, SessionStatus.LIVE]:
            return None
        
        session.status = SessionStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    # ============== Participant Management ==============
    
    async def join_session(
        self,
        session_id: int,
        student_id: int
    ) -> SessionParticipant | None:
        """Student joins a session."""
        session = await self.get_session(session_id)
        if not session or session.status not in [SessionStatus.SCHEDULED, SessionStatus.LIVE]:
            return None
        
        # Check max participants
        participant_count = len(session.participants)
        if participant_count >= session.max_participants:
            return None
        
        # Check if already joined
        existing = await self.get_participant(session_id, student_id)
        if existing:
            return existing
        
        participant = SessionParticipant(
            session_id=session_id,
            student_id=student_id
        )
        self.db.add(participant)
        await self.db.flush()
        await self.db.refresh(participant)
        return participant
    
    async def get_participant(
        self,
        session_id: int,
        student_id: int
    ) -> SessionParticipant | None:
        """Get a participant by session and student."""
        result = await self.db.execute(
            select(SessionParticipant).where(
                SessionParticipant.session_id == session_id,
                SessionParticipant.student_id == student_id
            )
        )
        return result.scalar_one_or_none()
    
    async def leave_session(
        self,
        session_id: int,
        student_id: int
    ) -> bool:
        """Student leaves a session."""
        participant = await self.get_participant(session_id, student_id)
        if not participant:
            return False
        
        participant.left_at = datetime.utcnow()
        await self.db.flush()
        return True
    
    async def get_participant_count(self, session_id: int) -> int:
        """Get the number of participants in a session."""
        result = await self.db.execute(
            select(func.count(SessionParticipant.id)).where(
                SessionParticipant.session_id == session_id,
                SessionParticipant.left_at == None
            )
        )
        return result.scalar() or 0
    
    # ============== Question Management ==============
    
    async def ask_question(
        self,
        session_id: int,
        student_id: int,
        question_text: str
    ) -> SessionQuestion | None:
        """Student asks a question."""
        session = await self.get_session(session_id)
        if not session or session.status != SessionStatus.LIVE:
            return None
        
        question = SessionQuestion(
            session_id=session_id,
            student_id=student_id,
            question_text=question_text
        )
        self.db.add(question)
        await self.db.flush()
        await self.db.refresh(question)
        return question
    
    async def get_pending_questions(
        self,
        session_id: int
    ) -> list[SessionQuestion]:
        """Get all pending questions in a session."""
        result = await self.db.execute(
            select(SessionQuestion).where(
                SessionQuestion.session_id == session_id,
                SessionQuestion.status == QuestionStatus.PENDING
            ).order_by(SessionQuestion.created_at)
        )
        return list(result.scalars().all())
    
    async def accept_question(
        self,
        question_id: int
    ) -> SessionQuestion | None:
        """Faculty accepts a question."""
        result = await self.db.execute(
            select(SessionQuestion).where(SessionQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return None
        
        question.status = QuestionStatus.ACCEPTED
        await self.db.flush()
        await self.db.refresh(question)
        return question
    
    async def answer_question(
        self,
        question_id: int,
        answer_text: str | None = None
    ) -> SessionQuestion | None:
        """Mark a question as answered."""
        result = await self.db.execute(
            select(SessionQuestion).where(SessionQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return None
        
        question.status = QuestionStatus.ANSWERED
        question.answer_text = answer_text
        question.answered_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(question)
        return question
    
    async def skip_question(
        self,
        question_id: int
    ) -> SessionQuestion | None:
        """Skip a question."""
        result = await self.db.execute(
            select(SessionQuestion).where(SessionQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return None
        
        question.status = QuestionStatus.SKIPPED
        await self.db.flush()
        await self.db.refresh(question)
        return question
    
    # ============== Summary ==============
    
    async def add_summary(
        self,
        session_id: int,
        summary_text: str,
        key_topics: str | None = None,
        created_by: int | None = None
    ) -> SessionSummary:
        """Add a post-session summary."""
        summary = SessionSummary(
            session_id=session_id,
            summary_text=summary_text,
            key_topics=key_topics,
            created_by=created_by
        )
        self.db.add(summary)
        await self.db.flush()
        await self.db.refresh(summary)
        return summary
    
    async def get_summary(self, session_id: int) -> SessionSummary | None:
        """Get the summary for a session."""
        result = await self.db.execute(
            select(SessionSummary).where(SessionSummary.session_id == session_id)
        )
        return result.scalar_one_or_none()
