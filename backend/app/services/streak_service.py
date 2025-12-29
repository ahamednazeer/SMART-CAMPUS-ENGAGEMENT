from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.streak_repository import StreakRepository, StreakRecoveryRepository
from app.repositories.user_repository import UserRepository
from app.repositories.reading_repository import DailyReadingLogRepository
from app.models.streak import Streak, StreakRecoveryRequest, RecoveryStatus
from app.models.user import User, StudentCategory
from app.schemas.streak import (
    StreakOut, StreakDashboard, RecoveryRequestCreate, RecoveryRequestOut,
    RecoveryReview, StreakAnalytics
)


class StreakService:
    """Service for streak management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.streak_repo = StreakRepository(db)
        self.recovery_repo = StreakRecoveryRepository(db)
        self.user_repo = UserRepository(db)
        self.log_repo = DailyReadingLogRepository(db)
    
    async def get_student_streak(self, student_id: int, pdf_id: int) -> StreakOut:
        """Get student's streak for a PDF."""
        streak = await self.streak_repo.get_or_create(student_id, pdf_id)
        return StreakOut.model_validate(streak)
    
    async def get_student_dashboard(self, student: User, pdf_id: int) -> StreakDashboard:
        """Get student's streak dashboard."""
        # First, evaluate any pending logs from past days
        await self.evaluate_student_pending_logs(student.id)

        streak = await self.streak_repo.get_or_create(student.id, pdf_id)
        all_streaks = await self.streak_repo.get_student_streaks(student.id)
        
        # Determine recovery options based on category
        can_request_recovery = (
            student.student_category == StudentCategory.HOSTELLER and 
            streak.is_broken and 
            not streak.recovery_used
        )
        
        can_auto_recover = (
            student.student_category == StudentCategory.DAY_SCHOLAR and
            streak.is_broken and
            not streak.recovery_used
        )
        
        return StreakDashboard(
            current_streak=streak.current_streak,
            max_streak=streak.max_streak,
            is_broken=streak.is_broken,
            can_request_recovery=can_request_recovery,
            can_auto_recover=can_auto_recover,
            recovery_used=streak.recovery_used,
            streak_history=[StreakOut.model_validate(s) for s in all_streaks],
        )
    
    async def update_streak(
        self, student_id: int, pdf_id: int, day_success: bool
    ) -> StreakOut:
        """Update streak after daily evaluation."""
        streak = await self.streak_repo.get_or_create(student_id, pdf_id)
        
        if day_success:
            # Success - increment streak
            streak.current_streak += 1
            streak.max_streak = max(streak.max_streak, streak.current_streak)
            streak.last_activity_date = date.today()
        else:
            # Failure - break streak
            streak.is_broken = True
            streak.current_streak = 0
        
        streak = await self.streak_repo.update(streak)
        return StreakOut.model_validate(streak)
    
    async def request_recovery(
        self, student: User, data: RecoveryRequestCreate
    ) -> RecoveryRequestOut:
        """Submit a streak recovery request (hostellers only)."""
        if student.student_category != StudentCategory.HOSTELLER:
            raise ValueError("Only hostellers can submit recovery requests")
        
        streak = await self.streak_repo.get_by_id(data.streak_id)
        if streak is None or streak.student_id != student.id:
            raise ValueError("Streak not found")
        
        if not streak.is_broken:
            raise ValueError("Streak is not broken")
        
        if streak.recovery_used:
            raise ValueError("Recovery already used for this streak")
        
        request = StreakRecoveryRequest(
            student_id=student.id,
            streak_id=data.streak_id,
            reason=data.reason,
        )
        
        request = await self.recovery_repo.create(request)
        return RecoveryRequestOut.model_validate(request)
    
    async def review_recovery(
        self, request_id: int, reviewer_id: int, data: RecoveryReview
    ) -> RecoveryRequestOut:
        """Admin reviews a recovery request."""
        request = await self.recovery_repo.get_by_id(request_id)
        if request is None:
            raise ValueError("Recovery request not found")
        
        if request.status != RecoveryStatus.PENDING:
            raise ValueError("Request already reviewed")
        
        request.status = data.status
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.admin_notes = data.admin_notes
        
        request = await self.recovery_repo.update(request)
        
        # If approved, restore streak
        if data.status == RecoveryStatus.APPROVED:
            streak = await self.streak_repo.get_by_id(request.streak_id)
            if streak:
                streak.is_broken = False
                streak.recovery_used = True
                await self.streak_repo.update(streak)
        
        return RecoveryRequestOut.model_validate(request)
    
    async def auto_recover_day_scholar(
        self, student_id: int, pdf_id: int, today_seconds: int
    ) -> bool:
        """Auto-recover day scholar streak if they read 20 minutes."""
        user = await self.user_repo.get_by_id(student_id)
        if user is None or user.student_category != StudentCategory.DAY_SCHOLAR:
            return False
        
        streak = await self.streak_repo.get_student_streak(student_id, pdf_id)
        if streak is None or not streak.is_broken or streak.recovery_used:
            return False
        
        # Check if read 20 minutes (1200 seconds)
        if today_seconds >= 1200:
            streak.is_broken = False
            streak.current_streak = 1
            streak.recovery_used = True
            streak.last_activity_date = date.today()
            await self.streak_repo.update(streak)
            return True
        
        return False
    
    async def get_analytics(self) -> StreakAnalytics:
        """Get streak analytics for admin."""
        active = await self.streak_repo.count_active()
        broken = await self.streak_repo.count_broken()
        avg = await self.streak_repo.avg_streak_length()
        pending = await self.recovery_repo.count_pending()
        
        total_students = await self.user_repo.count()
        
        return StreakAnalytics(
            total_students=total_students,
            active_streaks=active,
            broken_streaks=broken,
            avg_streak_length=avg,
            pending_recovery_requests=pending,
        )
    
    async def get_pending_requests(self) -> list[RecoveryRequestOut]:
        """Get all pending recovery requests."""
        requests = await self.recovery_repo.get_pending_requests()
        return [RecoveryRequestOut.model_validate(r) for r in requests]

    async def evaluate_student_pending_logs(self, student_id: int):
        """Evaluate pending logs and update streaks."""
        pending_logs = await self.log_repo.get_pending_logs_for_student(student_id)
        
        for log in pending_logs:
            # Update streak
            await self.update_streak(student_id, log.pdf_id, log.is_success)
            
            # Lock the log
            log.is_locked = True
            log.evaluated_at = datetime.now(timezone.utc)
            await self.log_repo.update(log)
