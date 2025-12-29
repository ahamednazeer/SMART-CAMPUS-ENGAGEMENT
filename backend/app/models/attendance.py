"""
Attendance system database models.
Supports location-based attendance with face recognition verification.
"""
import enum
from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import (
    String, Boolean, Enum, DateTime, Date, Time, Float, Integer,
    Text, LargeBinary, ForeignKey, UniqueConstraint, func, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ProfilePhotoStatus(str, enum.Enum):
    """Status of profile photo approval."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AttendanceStatus(str, enum.Enum):
    """Attendance status."""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    PENDING = "PENDING"  # Not marked yet, window still open


class FailureReason(str, enum.Enum):
    """Reasons for attendance failure."""
    OUTSIDE_CAMPUS = "OUTSIDE_CAMPUS"
    GPS_DISABLED = "GPS_DISABLED"
    LOW_GPS_ACCURACY = "LOW_GPS_ACCURACY"
    FACE_MISMATCH = "FACE_MISMATCH"
    MULTIPLE_FACES = "MULTIPLE_FACES"
    NO_FACE_DETECTED = "NO_FACE_DETECTED"
    PROFILE_NOT_APPROVED = "PROFILE_NOT_APPROVED"
    OUTSIDE_TIME_WINDOW = "OUTSIDE_TIME_WINDOW"
    ALREADY_MARKED = "ALREADY_MARKED"
    IMAGE_QUALITY_POOR = "IMAGE_QUALITY_POOR"
    FACE_OBSTRUCTED = "FACE_OBSTRUCTED"


class ProfilePhoto(Base):
    """Student profile photo for face recognition reference."""
    
    __tablename__ = "profile_photos"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # File storage
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Face encoding for matching (stored as JSON string of list)
    face_encoding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Approval status
    status: Mapped[ProfilePhotoStatus] = mapped_column(
        Enum(ProfilePhotoStatus),
        default=ProfilePhotoStatus.PENDING
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id], backref="profile_photos")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    __table_args__ = (
        UniqueConstraint('student_id', 'status', name='uq_student_approved_photo'),
    )


class CampusGeofence(Base):
    """Campus boundary definition for location verification."""
    
    __tablename__ = "campus_geofences"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Center coordinates
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Radius in meters
    radius_meters: Mapped[float] = mapped_column(Float, nullable=False, default=500.0)
    
    # GPS accuracy threshold in meters
    accuracy_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    
    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationship
    creator = relationship("User", backref="created_geofences")


class AttendanceWindow(Base):
    """Time windows when attendance can be marked."""
    
    __tablename__ = "attendance_windows"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Time window
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # Days of week (JSON array of integers, 0=Monday, 6=Sunday)
    days_of_week: Mapped[str] = mapped_column(
        String(50),
        default="[0,1,2,3,4,5]"  # Monday to Saturday
    )
    
    # Optional: target specific student category
    student_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class AttendanceRecord(Base):
    """Daily attendance record for each student."""
    
    __tablename__ = "attendance_records"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Date of attendance
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Status
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus),
        default=AttendanceStatus.ABSENT
    )
    
    # Location snapshot when marked present
    location_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Verification details
    face_match_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    marked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationship
    student = relationship("User", backref="attendance_records")
    
    __table_args__ = (
        UniqueConstraint('student_id', 'attendance_date', name='uq_student_daily_attendance'),
    )


class AttendanceAttempt(Base):
    """Log of all attendance attempts for audit purposes."""
    
    __tablename__ = "attendance_attempts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Attempt timestamp
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    
    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[Optional[FailureReason]] = mapped_column(
        Enum(FailureReason),
        nullable=True
    )
    failure_details: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Location data at attempt
    location_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Captured image path (for failed attempts review)
    captured_image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Face match score (even for failures, for debugging)
    face_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Geofence used for validation
    geofence_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campus_geofences.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationship
    student = relationship("User", backref="attendance_attempts")
    geofence = relationship("CampusGeofence")


class Holiday(Base):
    """Admin-configured holidays and non-working days."""
    
    __tablename__ = "holidays"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Holiday date
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    
    # Holiday name/description
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Holiday type (can be used for categorization)
    holiday_type: Mapped[str] = mapped_column(
        String(50), 
        default="GENERAL"  # GENERAL, NATIONAL, EXAM, VACATION, etc.
    )
    
    # Is this a recurring annual holiday?
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationship
    creator = relationship("User", backref="created_holidays")


class AttendanceSettings(Base):
    """Admin-configurable attendance settings including academic year dates."""
    
    __tablename__ = "attendance_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Setting key-value pair
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Audit
    updated_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
