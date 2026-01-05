"""
Collaborative Whiteboard models for real-time group explanation.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, JSON, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class WhiteboardStatus(str, enum.Enum):
    """Whiteboard session status."""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class WhiteboardPermission(str, enum.Enum):
    """Participant permissions."""
    VIEW = "VIEW"
    DRAW = "DRAW"
    EXPLAIN = "EXPLAIN"  # Can draw + voice


class WhiteboardSession(Base):
    """Collaborative whiteboard session."""
    
    __tablename__ = "whiteboard_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Topic/course link
    course_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Session creator
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    status: Mapped[WhiteboardStatus] = mapped_column(
        Enum(WhiteboardStatus), default=WhiteboardStatus.ACTIVE
    )
    
    # Canvas data (final state after closing)
    canvas_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Read-only after closing for revision
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Jitsi voice room for explanations
    voice_room_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    participants = relationship("WhiteboardParticipant", back_populates="session", cascade="all, delete-orphan")
    snapshots = relationship("WhiteboardSnapshot", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<WhiteboardSession {self.title}>"


class WhiteboardParticipant(Base):
    """Participant in a whiteboard session."""
    
    __tablename__ = "whiteboard_participants"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("whiteboard_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    permission: Mapped[WhiteboardPermission] = mapped_column(
        Enum(WhiteboardPermission), default=WhiteboardPermission.VIEW
    )
    
    # Draw color assignment for identification
    draw_color: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g., "#FF5733"
    
    invited_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    session = relationship("WhiteboardSession", back_populates="participants")
    
    def __repr__(self) -> str:
        return f"<WhiteboardParticipant user={self.user_id} session={self.session_id}>"


class WhiteboardSnapshot(Base):
    """Saved snapshot of whiteboard state."""
    
    __tablename__ = "whiteboard_snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("whiteboard_sessions.id", ondelete="CASCADE"), index=True
    )
    
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    canvas_data: Mapped[dict] = mapped_column(JSON)
    
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    session = relationship("WhiteboardSession", back_populates="snapshots")
    
    def __repr__(self) -> str:
        return f"<WhiteboardSnapshot session={self.session_id}>"
