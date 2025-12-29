from datetime import datetime, date
from pydantic import BaseModel


class SessionStart(BaseModel):
    """Start reading session request."""
    pdf_id: int


class SessionEvent(BaseModel):
    """Pause/resume event request."""
    session_id: int



class HeartbeatIn(BaseModel):
    """Heartbeat request with activity delta."""
    delta_seconds: int


class SessionEnd(BaseModel):
    """End reading session request."""
    final_delta_seconds: int = 0


class SessionOut(BaseModel):
    """Reading session output schema."""
    id: int
    student_id: int
    pdf_id: int
    session_date: date
    start_time: datetime
    end_time: datetime | None
    valid_duration_seconds: int
    status: str
    is_valid: bool
    is_completed: bool
    
    class Config:
        from_attributes = True


class DailyLogOut(BaseModel):
    """Daily reading log output schema."""
    id: int
    student_id: int
    pdf_id: int
    log_date: date
    total_valid_seconds: int
    is_success: bool
    is_locked: bool
    
    class Config:
        from_attributes = True


class ReadingProgressOut(BaseModel):
    """Student's reading progress for a PDF."""
    pdf_id: int
    today_reading_seconds: int
    total_reading_seconds: int
    today_required_seconds: int
    today_completed: bool
    active_session: SessionOut | None = None


class ReadingHistoryOut(BaseModel):
    """Student's reading history."""
    daily_logs: list[DailyLogOut]
    total_days: int
    successful_days: int
