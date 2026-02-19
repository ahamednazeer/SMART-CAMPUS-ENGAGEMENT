"""Hostel models for hostel management system."""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Enum, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class HostelType(str, enum.Enum):
    """Hostel type for gender matching."""
    BOYS = "BOYS"
    GIRLS = "GIRLS"
    CO_ED = "CO_ED"


class Hostel(Base):
    """Hostel entity."""
    
    __tablename__ = "hostels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)

    # Warden assignment (FK to users table)
    warden_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    hostel_type: Mapped[HostelType] = mapped_column(
        Enum(HostelType, native_enum=False), default=HostelType.CO_ED, nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    rooms: Mapped[list["HostelRoom"]] = relationship(
        "HostelRoom", back_populates="hostel", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["HostelAssignment"]] = relationship(
        "HostelAssignment", back_populates="hostel"
    )
    
    def __repr__(self) -> str:
        return f"<Hostel {self.name}>"


class HostelRoom(Base):
    """Room within a hostel."""
    
    __tablename__ = "hostel_rooms"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hostels.id", ondelete="CASCADE"), index=True
    )
    room_number: Mapped[str] = mapped_column(String(20))
    floor: Mapped[int] = mapped_column(Integer, default=0)
    capacity: Mapped[int] = mapped_column(Integer, default=2)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="rooms")
    assignments: Mapped[list["HostelAssignment"]] = relationship(
        "HostelAssignment", back_populates="room"
    )
    
    def __repr__(self) -> str:
        return f"<HostelRoom {self.room_number} in Hostel {self.hostel_id}>"


class HostelAssignment(Base):
    """Student-Room assignment."""
    
    __tablename__ = "hostel_assignments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Student (globally unique row; assignment is reactivated/updated on re-assign)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, index=True
    )
    
    # Hostel and Room
    hostel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hostels.id"), index=True
    )
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hostel_rooms.id"), index=True
    )
    
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    hostel: Mapped["Hostel"] = relationship("Hostel", back_populates="assignments")
    room: Mapped["HostelRoom"] = relationship("HostelRoom", back_populates="assignments")
    
    def __repr__(self) -> str:
        return f"<HostelAssignment Student {self.student_id} -> Room {self.room_id}>"


class HostelAssignmentBatch(Base):
    """Batch record for auto-assign confirmations."""

    __tablename__ = "hostel_assignment_batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hostel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hostels.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    assigned_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    assigned: Mapped[list] = mapped_column(JSONB, default=list)
    skipped: Mapped[list] = mapped_column(JSONB, default=list)

    def __repr__(self) -> str:
        return f"<HostelAssignmentBatch Hostel {self.hostel_id} Count {self.assigned_count}>"
