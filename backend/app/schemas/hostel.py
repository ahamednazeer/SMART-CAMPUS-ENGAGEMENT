"""Pydantic schemas for hostel management."""
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== HOSTEL SCHEMAS ====================

class HostelBase(BaseModel):
    """Base hostel schema."""
    name: str = Field(..., min_length=1, max_length=100)
    address: str | None = None
    capacity: int = Field(default=100, ge=1)


class HostelCreate(HostelBase):
    """Hostel creation schema."""
    pass


class HostelUpdate(BaseModel):
    """Hostel update schema."""
    name: str | None = None
    address: str | None = None
    capacity: int | None = Field(default=None, ge=1)
    warden_id: int | None = None
    is_active: bool | None = None


class HostelOut(HostelBase):
    """Hostel output schema."""
    id: int
    warden_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HostelWithDetails(HostelOut):
    """Hostel with room count and occupancy."""
    room_count: int = 0
    occupied_beds: int = 0
    warden_name: str | None = None


# ==================== ROOM SCHEMAS ====================

class HostelRoomBase(BaseModel):
    """Base room schema."""
    room_number: str = Field(..., min_length=1, max_length=20)
    floor: int = Field(default=0, ge=0)
    capacity: int = Field(default=2, ge=1)


class HostelRoomCreate(HostelRoomBase):
    """Room creation schema."""
    hostel_id: int


class HostelRoomUpdate(BaseModel):
    """Room update schema."""
    room_number: str | None = None
    floor: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class HostelRoomOut(HostelRoomBase):
    """Room output schema."""
    id: int
    hostel_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HostelRoomWithOccupancy(HostelRoomOut):
    """Room with occupancy info."""
    current_occupancy: int = 0
    available_beds: int = 0


# ==================== ASSIGNMENT SCHEMAS ====================

class HostelAssignmentBase(BaseModel):
    """Base assignment schema."""
    student_id: int
    hostel_id: int
    room_id: int


class HostelAssignmentCreate(HostelAssignmentBase):
    """Assignment creation schema."""
    pass


class HostelAssignmentOut(HostelAssignmentBase):
    """Assignment output schema."""
    id: int
    assigned_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class HostelAssignmentWithDetails(HostelAssignmentOut):
    """Assignment with student and room names."""
    student_name: str
    student_register_number: str | None
    hostel_name: str
    room_number: str


class StudentHostelInfo(BaseModel):
    """Student's hostel info for dashboard."""
    is_assigned: bool = False
    hostel_name: str | None = None
    hostel_address: str | None = None
    room_number: str | None = None
    floor: int | None = None
    warden_name: str | None = None
    assigned_at: datetime | None = None
