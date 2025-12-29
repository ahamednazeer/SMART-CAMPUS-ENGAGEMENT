"""Maintenance complaint models for hostel maintenance management."""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Enum, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class MaintenanceCategory(str, enum.Enum):
    """Maintenance complaint category."""
    ELECTRICAL = "ELECTRICAL"
    PLUMBING = "PLUMBING"
    FURNITURE = "FURNITURE"
    CLEANING = "CLEANING"
    AC_COOLING = "AC_COOLING"
    NETWORK = "NETWORK"
    OTHER = "OTHER"


class MaintenanceStatus(str, enum.Enum):
    """Maintenance complaint status."""
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class HostelMaintenance(Base):
    """Maintenance complaint entity."""
    
    __tablename__ = "hostel_maintenance"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Student who raised complaint
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True
    )
    
    # Location
    hostel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hostels.id"), index=True
    )
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hostel_rooms.id"), index=True
    )
    
    # Complaint details
    category: Mapped[MaintenanceCategory] = mapped_column(Enum(MaintenanceCategory))
    description: Mapped[str] = mapped_column(Text)
    
    # Status tracking
    status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus), default=MaintenanceStatus.PENDING
    )
    
    # Assignment
    assigned_to: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Resolution
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
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
        return f"<HostelMaintenance {self.id} - {self.category.value} - {self.status.value}>"
