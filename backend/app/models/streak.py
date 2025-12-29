import enum
from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, Text, Enum, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RecoveryStatus(str, enum.Enum):
    """Status for streak recovery requests."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Streak(Base):
    """Student reading streak tracking."""
    
    __tablename__ = "streaks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    pdf_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pdfs.id", ondelete="CASCADE"), index=True
    )
    
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    
    is_broken: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Track recovery attempts (day scholars get one auto-recovery per cycle)
    recovery_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<Streak student={self.student_id} current={self.current_streak}>"


class StreakRecoveryRequest(Base):
    """Recovery request for broken streaks (hostellers only)."""
    
    __tablename__ = "streak_recovery_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    streak_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("streaks.id", ondelete="CASCADE"), index=True
    )
    
    reason: Mapped[str] = mapped_column(Text)
    
    status: Mapped[RecoveryStatus] = mapped_column(
        Enum(RecoveryStatus), default=RecoveryStatus.PENDING
    )
    
    reviewed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<StreakRecoveryRequest student={self.student_id} status={self.status.value}>"
