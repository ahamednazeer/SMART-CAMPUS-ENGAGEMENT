from datetime import datetime, date
from pydantic import BaseModel
from app.models.streak import RecoveryStatus


class StreakOut(BaseModel):
    """Streak output schema."""
    id: int
    student_id: int
    pdf_id: int
    current_streak: int
    max_streak: int
    is_broken: bool
    recovery_used: bool
    last_activity_date: date | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StreakDashboard(BaseModel):
    """Student streak dashboard."""
    current_streak: int
    max_streak: int
    is_broken: bool
    can_request_recovery: bool  # For hostellers
    can_auto_recover: bool  # For day scholars
    recovery_used: bool
    streak_history: list[StreakOut]


class RecoveryRequestCreate(BaseModel):
    """Streak recovery request creation."""
    streak_id: int
    reason: str


class RecoveryRequestOut(BaseModel):
    """Recovery request output schema."""
    id: int
    student_id: int
    streak_id: int
    reason: str
    status: RecoveryStatus
    reviewed_by: int | None
    reviewed_at: datetime | None
    admin_notes: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RecoveryReview(BaseModel):
    """Admin review of recovery request."""
    status: RecoveryStatus
    admin_notes: str | None = None


class StreakAnalytics(BaseModel):
    """Admin streak analytics."""
    total_students: int
    active_streaks: int
    broken_streaks: int
    avg_streak_length: float
    pending_recovery_requests: int
