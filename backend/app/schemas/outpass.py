"""Pydantic schemas for outpass management."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.outpass import OutpassStatus


# ==================== OUTPASS REQUEST SCHEMAS ====================

class OutpassCreate(BaseModel):
    """Outpass creation schema (student submission)."""
    reason: str = Field(..., min_length=10, max_length=500)
    destination: str = Field(..., min_length=2, max_length=255)
    start_datetime: datetime
    end_datetime: datetime
    emergency_contact: str = Field(..., min_length=10, max_length=20)

    @field_validator('end_datetime')
    @classmethod
    def end_after_start(cls, v, info):
        """Ensure end datetime is after start datetime."""
        if 'start_datetime' in info.data and v <= info.data['start_datetime']:
            raise ValueError('End datetime must be after start datetime')
        return v

    @field_validator('start_datetime')
    @classmethod
    def start_in_future(cls, v):
        """Ensure start datetime is in the future."""
        if v <= datetime.now(v.tzinfo):
            raise ValueError('Start datetime must be in the future')
        return v


class OutpassUpdate(BaseModel):
    """Outpass update schema (before submission)."""
    reason: str | None = Field(default=None, min_length=10, max_length=500)
    destination: str | None = Field(default=None, min_length=2, max_length=255)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    emergency_contact: str | None = Field(default=None, min_length=10, max_length=20)


class OutpassOut(BaseModel):
    """Outpass output schema."""
    id: int
    student_id: int
    reason: str
    destination: str
    start_datetime: datetime
    end_datetime: datetime
    emergency_contact: str
    status: OutpassStatus
    rejection_reason: str | None
    reviewed_by: int | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OutpassWithStudentDetails(OutpassOut):
    """Outpass with student information (for warden view)."""
    student_name: str
    student_register_number: str | None
    student_room_number: str | None
    student_department: str | None


class OutpassListOut(BaseModel):
    """Paginated list of outpass requests."""
    outpasses: list[OutpassOut]
    total: int
    page: int
    page_size: int


# ==================== APPROVAL SCHEMAS ====================

class OutpassApproval(BaseModel):
    """Outpass approval schema."""
    approved: bool
    rejection_reason: str | None = Field(default=None, max_length=500)

    @field_validator('rejection_reason')
    @classmethod
    def rejection_reason_required_on_reject(cls, v, info):
        """Require rejection reason when not approved."""
        if 'approved' in info.data and not info.data['approved'] and not v:
            raise ValueError('Rejection reason is required when rejecting')
        return v


# ==================== LOG SCHEMAS ====================

class OutpassLogOut(BaseModel):
    """Outpass log output schema."""
    id: int
    outpass_id: int
    previous_status: OutpassStatus | None
    new_status: OutpassStatus
    changed_by: int
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== SUMMARY SCHEMAS ====================

class OutpassSummary(BaseModel):
    """Summary of student's outpass usage."""
    total_requests: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0
    current_month_count: int = 0
    monthly_limit: int = 4  # Configurable limit
