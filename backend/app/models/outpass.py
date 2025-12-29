"""Outpass request models for hostel outpass management."""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Enum, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class OutpassStatus(str, enum.Enum):
    """Outpass request status enumeration."""
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CLOSED = "CLOSED"


class OutpassRequest(Base):
    """Outpass request entity."""
    
    __tablename__ = "outpass_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Student who requested
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True
    )
    
    # Request details
    reason: Mapped[str] = mapped_column(Text)
    destination: Mapped[str] = mapped_column(String(255))
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    emergency_contact: Mapped[str] = mapped_column(String(20))
    
    # Status tracking
    status: Mapped[OutpassStatus] = mapped_column(
        Enum(OutpassStatus), default=OutpassStatus.SUBMITTED
    )
    
    # Rejection details (optional)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Review details
    reviewed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<OutpassRequest {self.id} - {self.status.value}>"


class OutpassLog(Base):
    """Audit log for outpass status changes."""
    
    __tablename__ = "outpass_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    outpass_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("outpass_requests.id", ondelete="CASCADE"), index=True
    )
    
    previous_status: Mapped[OutpassStatus | None] = mapped_column(
        Enum(OutpassStatus), nullable=True
    )
    new_status: Mapped[OutpassStatus] = mapped_column(Enum(OutpassStatus))
    
    changed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<OutpassLog {self.id} - {self.new_status.value}>"
