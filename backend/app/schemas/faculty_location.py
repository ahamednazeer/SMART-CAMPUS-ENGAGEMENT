"""Schemas for Faculty Location & Availability module."""
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.faculty_location import AvailabilityStatus, VisibilityLevel


# ============ Campus Building Schemas ============

class CampusBuildingCreate(BaseModel):
    """Schema for creating a campus building."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    floor_count: int = Field(default=1, ge=1)


class CampusBuildingUpdate(BaseModel):
    """Schema for updating a campus building."""
    name: str | None = None
    code: str | None = None
    description: str | None = None
    floor_count: int | None = None
    is_active: bool | None = None


class CampusBuildingOut(BaseModel):
    """Schema for campus building output."""
    id: int
    name: str
    code: str
    description: str | None
    floor_count: int
    is_active: bool
    
    class Config:
        from_attributes = True


# ============ Faculty Availability Schemas ============

class FacultyAvailabilityUpdate(BaseModel):
    """Schema for faculty updating their availability settings."""
    is_sharing_enabled: bool | None = None
    availability_status: AvailabilityStatus | None = None
    visibility_level: VisibilityLevel | None = None
    status_message: str | None = Field(None, max_length=200)


class FacultyLocationRefresh(BaseModel):
    """Schema for refreshing faculty last-seen location."""
    building_id: int
    floor: int | None = None


class FacultySettingsOut(BaseModel):
    """Schema for faculty's own settings view."""
    id: int
    faculty_id: int
    is_sharing_enabled: bool
    availability_status: AvailabilityStatus
    visibility_level: VisibilityLevel
    status_message: str | None
    last_seen_building: CampusBuildingOut | None
    last_seen_floor: int | None
    last_seen_at: datetime | None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FacultyLocationOut(BaseModel):
    """Schema for student-facing faculty location view (limited info)."""
    faculty_id: int
    faculty_name: str
    department: str | None
    availability_status: AvailabilityStatus
    status_message: str | None
    last_seen_building_name: str | None
    last_seen_floor: int | None
    last_seen_at: datetime | None
    # Computed field for time since last seen
    last_seen_minutes_ago: int | None = None


class FacultyLocationListOut(BaseModel):
    """List of faculty with pagination."""
    faculty: list[FacultyLocationOut]
    total: int
    page: int
    page_size: int


# ============ Admin Schemas ============

class AdminFacultyLocationOut(BaseModel):
    """Schema for admin view of faculty with full settings."""
    faculty_id: int
    username: str
    faculty_name: str
    email: str
    department: str | None
    is_sharing_enabled: bool
    availability_status: AvailabilityStatus
    visibility_level: VisibilityLevel
    status_message: str | None
    last_seen_building_name: str | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminFacultyListOut(BaseModel):
    """Admin list of all faculty."""
    faculty: list[AdminFacultyLocationOut]
    total: int


class FacultyLocationStats(BaseModel):
    """System-level usage statistics for admin."""
    total_faculty: int
    sharing_enabled_count: int
    available_count: int
    busy_count: int
    offline_count: int
