"""Faculty Location & Availability models for Module 5."""
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum, DateTime, ForeignKey, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AvailabilityStatus(str, enum.Enum):
    """Faculty availability status options."""
    AVAILABLE = "AVAILABLE"  # Can meet students
    BUSY = "BUSY"  # On campus but not available
    OFFLINE = "OFFLINE"  # Not available


class VisibilityLevel(str, enum.Enum):
    """Faculty location visibility levels."""
    ALL_STUDENTS = "ALL_STUDENTS"  # Visible to all students
    SAME_DEPARTMENT = "SAME_DEPARTMENT"  # Only students in same department
    ADMIN_ONLY = "ADMIN_ONLY"  # Only visible to admin
    HIDDEN = "HIDDEN"  # Not visible to anyone


class CampusBuilding(Base):
    """Campus building/location model for tracking last-seen locations."""
    
    __tablename__ = "campus_buildings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # e.g., "IT", "MAIN", "LIB"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    floor_count: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<CampusBuilding {self.code}: {self.name}>"


class FacultyAvailability(Base):
    """Faculty availability and location sharing settings."""
    
    __tablename__ = "faculty_availability"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign key to users table (faculty/staff)
    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    
    # Privacy & Sharing Settings
    is_sharing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    visibility_level: Mapped[VisibilityLevel] = mapped_column(
        Enum(VisibilityLevel), default=VisibilityLevel.ALL_STUDENTS
    )
    
    # Current Status
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus), default=AvailabilityStatus.OFFLINE
    )
    status_message: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Last Seen Location (only building, not exact coordinates)
    last_seen_building_id: Mapped[int | None] = mapped_column(
        ForeignKey("campus_buildings.id", ondelete="SET NULL"), nullable=True
    )
    last_seen_floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    faculty = relationship("User", backref="faculty_availability", foreign_keys=[faculty_id])
    last_seen_building = relationship("CampusBuilding", backref="faculty_last_seen")
    
    def __repr__(self) -> str:
        return f"<FacultyAvailability faculty_id={self.faculty_id} status={self.availability_status.value}>"
