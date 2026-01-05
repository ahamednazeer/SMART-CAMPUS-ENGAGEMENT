"""
Live Doubt Session models for faculty office hours.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SessionStatus(str, enum.Enum):
    """Doubt session status."""
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"


class QuestionStatus(str, enum.Enum):
    """Question request status."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    ANSWERED = "ANSWERED"
    SKIPPED = "SKIPPED"


class DoubtSession(Base):
    """Live doubt session scheduled by faculty."""
    
    __tablename__ = "doubt_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    faculty_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    # Course/subject link
    course_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    max_participants: Mapped[int] = mapped_column(Integer, default=50)
    
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.SCHEDULED
    )
    
    # Jitsi/video room integration
    room_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    room_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Session end data
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    questions = relationship("SessionQuestion", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<DoubtSession {self.title} by faculty={self.faculty_id}>"


class SessionParticipant(Base):
    """Student participating in a doubt session."""
    
    __tablename__ = "session_participants"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doubt_sessions.id", ondelete="CASCADE"), index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("DoubtSession", back_populates="participants")
    
    def __repr__(self) -> str:
        return f"<SessionParticipant student={self.student_id} session={self.session_id}>"


class SessionQuestion(Base):
    """Question raised by a student during a doubt session."""
    
    __tablename__ = "session_questions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doubt_sessions.id", ondelete="CASCADE"), index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    question_text: Mapped[str] = mapped_column(Text)
    
    status: Mapped[QuestionStatus] = mapped_column(
        Enum(QuestionStatus), default=QuestionStatus.PENDING
    )
    
    # Faculty response
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    session = relationship("DoubtSession", back_populates="questions")
    
    def __repr__(self) -> str:
        return f"<SessionQuestion id={self.id} session={self.session_id}>"


class SessionSummary(Base):
    """Post-session summary (optional)."""
    
    __tablename__ = "session_summaries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doubt_sessions.id", ondelete="CASCADE"), unique=True, index=True
    )
    
    summary_text: Mapped[str] = mapped_column(Text)
    key_topics: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of topics
    
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<SessionSummary session={self.session_id}>"
