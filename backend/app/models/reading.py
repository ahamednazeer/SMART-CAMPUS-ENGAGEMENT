from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ReadingSession(Base):
    """Individual reading session for tracking active reading time."""
    
    __tablename__ = "reading_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    pdf_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pdfs.id", ondelete="CASCADE"), index=True
    )
    
    session_date: Mapped[date] = mapped_column(Date, index=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Active reading time in seconds (excluding pauses)
    valid_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Track pause/resume events
    pause_events: Mapped[list | None] = mapped_column(JSON, nullable=True)  # List of timestamps
    resume_events: Mapped[list | None] = mapped_column(JSON, nullable=True)  # List of timestamps
    
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status: active, paused, completed
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<ReadingSession student={self.student_id} pdf={self.pdf_id} date={self.session_date}>"


class DailyReadingLog(Base):
    """Daily aggregated reading log for streak calculation."""
    
    __tablename__ = "daily_reading_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    pdf_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pdfs.id", ondelete="CASCADE"), index=True
    )
    
    log_date: Mapped[date] = mapped_column(Date, index=True)
    
    # Total valid reading time in seconds for the day
    total_valid_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Whether the minimum reading time was achieved
    is_success: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Once evaluated, the day is locked
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<DailyReadingLog student={self.student_id} date={self.log_date} success={self.is_success}>"
