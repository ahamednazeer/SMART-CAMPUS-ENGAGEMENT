"""
Attendance system Pydantic schemas for API request/response validation.
"""
from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json

from app.models.attendance import ProfilePhotoStatus, AttendanceStatus, FailureReason


# ============== Profile Photo Schemas ==============

class ProfilePhotoUpload(BaseModel):
    """Schema for profile photo upload - file handled separately by FastAPI."""
    pass


class ProfilePhotoOut(BaseModel):
    """Response schema for profile photo."""
    id: int
    student_id: int
    filename: str
    status: ProfilePhotoStatus
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ProfilePhotoApproval(BaseModel):
    """Schema for admin approving/rejecting a photo."""
    approved: bool
    rejection_reason: Optional[str] = None


class ProfilePhotoListOut(BaseModel):
    """List of profile photos with count."""
    photos: List[ProfilePhotoOut]
    total: int


# ============== Geofence Schemas ==============

class GeofenceCreate(BaseModel):
    """Schema for creating a campus geofence."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(default=500.0, ge=10, le=10000)
    accuracy_threshold: float = Field(default=50.0, ge=5, le=1000)
    is_primary: bool = False


class GeofenceUpdate(BaseModel):
    """Schema for updating a geofence."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_meters: Optional[float] = Field(None, ge=10, le=10000)
    accuracy_threshold: Optional[float] = Field(None, ge=5, le=1000)
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None


class GeofenceOut(BaseModel):
    """Response schema for geofence."""
    id: int
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius_meters: float
    accuracy_threshold: float
    is_active: bool
    is_primary: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class GeofenceListOut(BaseModel):
    """List of geofences."""
    geofences: List[GeofenceOut]
    total: int


# ============== Attendance Window Schemas ==============

class AttendanceWindowCreate(BaseModel):
    """Schema for creating an attendance time window."""
    name: str = Field(..., min_length=1, max_length=100)
    start_time: time
    end_time: time
    days_of_week: List[int] = Field(default=[0, 1, 2, 3, 4, 5])  # Mon-Sat
    student_category: Optional[str] = None
    is_active: bool = True
    
    @field_validator('days_of_week')
    @classmethod
    def validate_days(cls, v):
        if not all(0 <= d <= 6 for d in v):
            raise ValueError("Days must be between 0 (Monday) and 6 (Sunday)")
        return v


class AttendanceWindowUpdate(BaseModel):
    """Schema for updating an attendance window."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: Optional[List[int]] = None
    student_category: Optional[str] = None
    is_active: Optional[bool] = None


class AttendanceWindowOut(BaseModel):
    """Response schema for attendance window."""
    id: int
    name: str
    start_time: time
    end_time: time
    days_of_week: List[int]
    student_category: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
    @field_validator('days_of_week', mode='before')
    @classmethod
    def parse_days(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class AttendanceWindowListOut(BaseModel):
    """List of attendance windows."""
    windows: List[AttendanceWindowOut]
    total: int


# ============== Attendance Marking Schemas ==============

class LocationData(BaseModel):
    """GPS location data from frontend."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: float = Field(..., ge=0)  # in meters


class AttendanceMarkRequest(BaseModel):
    """Request to mark attendance - image handled separately."""
    location: LocationData


class AttendancePreCheckOut(BaseModel):
    """Pre-check status before allowing attendance marking."""
    can_mark: bool
    blockers: List[str] = []  # List of reasons why attendance can't be marked
    profile_approved: bool
    within_time_window: bool
    already_marked_today: bool


class AttendanceMarkResult(BaseModel):
    """Result of attendance marking attempt."""
    success: bool
    message: str
    attendance_status: Optional[AttendanceStatus] = None
    failure_reason: Optional[FailureReason] = None
    face_match_score: Optional[float] = None


# ============== Attendance Record Schemas ==============

class AttendanceRecordOut(BaseModel):
    """Response schema for attendance record."""
    id: Optional[int] = None
    student_id: int
    attendance_date: date
    status: AttendanceStatus
    marked_at: Optional[datetime] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    face_match_confidence: Optional[float] = None
    
    model_config = {"from_attributes": True}


class AttendanceRecordListOut(BaseModel):
    """List of attendance records."""
    records: List[AttendanceRecordOut]
    total: int


# ============== Attendance Attempt Schemas ==============

class AttendanceAttemptOut(BaseModel):
    """Response schema for attendance attempt (audit log)."""
    id: int
    student_id: int
    attempted_at: datetime
    success: bool
    failure_reason: Optional[FailureReason] = None
    failure_details: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    face_match_score: Optional[float] = None
    
    model_config = {"from_attributes": True}


class AttendanceAttemptListOut(BaseModel):
    """List of attendance attempts."""
    attempts: List[AttendanceAttemptOut]
    total: int


# ============== Dashboard Schemas ==============

class AttendanceDashboardStats(BaseModel):
    """Admin dashboard attendance statistics."""
    date: date
    total_students: int
    present_count: int
    absent_count: int
    failed_attempts_count: int
    attendance_percentage: float


class StudentAttendanceSummary(BaseModel):
    """Student's attendance summary."""
    student_id: int
    student_name: str
    register_number: Optional[str] = None
    total_days: int
    present_days: int
    absent_days: int
    attendance_percentage: float


# ============== Detailed Attendance Schemas ==============

class StudentDetailedAttendance(BaseModel):
    """Detailed attendance for a single student (for admin view)."""
    student_id: int
    student_name: str
    register_number: Optional[str] = None
    department: Optional[str] = None
    status: AttendanceStatus
    marked_at: Optional[datetime] = None
    face_match_confidence: Optional[float] = None


class DetailedAttendanceListOut(BaseModel):
    """List of students with their attendance status for a date."""
    date: date
    students: List[StudentDetailedAttendance]
    present_count: int
    absent_count: int
    pending_count: int = 0
    total_students: int


class StudentAttendanceStatsOut(BaseModel):
    """Student's own attendance statistics."""
    student_id: int
    student_name: str
    register_number: Optional[str] = None
    start_date: date
    end_date: date
    total_working_days: int
    holidays_count: int = 0
    present_days: int
    absent_days: int
    attendance_percentage: float
    recent_records: List[AttendanceRecordOut]
    holidays: List["HolidayOut"] = []


# ============== Holiday/Calendar Schemas ==============

class HolidayCreate(BaseModel):
    """Create a new holiday/non-working day."""
    date: date
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    holiday_type: str = "GENERAL"
    is_recurring: bool = False


class HolidayUpdate(BaseModel):
    """Update holiday details."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    holiday_type: Optional[str] = None
    is_recurring: Optional[bool] = None


class HolidayOut(BaseModel):
    """Holiday output."""
    id: int
    date: date
    name: str
    description: Optional[str] = None
    holiday_type: str
    is_recurring: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HolidayListOut(BaseModel):
    """List of holidays."""
    holidays: List[HolidayOut]
    total: int


class BulkHolidayCreate(BaseModel):
    """Bulk create holidays from pasted text."""
    text: str = Field(..., description="Tab or comma separated text: Date, Day, Holiday Name")
    year: int = Field(..., description="Year for the holidays")


# ============== Academic Year Settings Schemas ==============

class AcademicYearSettingsUpdate(BaseModel):
    """Update academic year settings."""
    start_date: date
    end_date: date


class AcademicYearSettingsOut(BaseModel):
    """Academic year settings output."""
    start_date: date
    end_date: date
    updated_at: Optional[datetime] = None
