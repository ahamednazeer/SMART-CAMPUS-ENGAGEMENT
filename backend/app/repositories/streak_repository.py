from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.streak import Streak, StreakRecoveryRequest, RecoveryStatus


class StreakRepository:
    """Repository for streak data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, streak_id: int) -> Streak | None:
        """Get streak by ID."""
        result = await self.db.execute(select(Streak).where(Streak.id == streak_id))
        return result.scalar_one_or_none()
    
    async def get_student_streak(self, student_id: int, pdf_id: int) -> Streak | None:
        """Get student's streak for a PDF."""
        result = await self.db.execute(
            select(Streak).where(
                Streak.student_id == student_id,
                Streak.pdf_id == pdf_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_student_streaks(self, student_id: int) -> list[Streak]:
        """Get all streaks for a student."""
        result = await self.db.execute(
            select(Streak).where(Streak.student_id == student_id)
        )
        return list(result.scalars().all())
    
    async def get_active_streaks(self) -> list[Streak]:
        """Get all active (non-broken) streaks."""
        result = await self.db.execute(
            select(Streak).where(Streak.is_broken == False)
        )
        return list(result.scalars().all())
    
    async def count_active(self) -> int:
        """Count active streaks."""
        result = await self.db.execute(
            select(func.count(Streak.id)).where(Streak.is_broken == False)
        )
        return result.scalar() or 0
    
    async def count_broken(self) -> int:
        """Count broken streaks."""
        result = await self.db.execute(
            select(func.count(Streak.id)).where(Streak.is_broken == True)
        )
        return result.scalar() or 0
    
    async def avg_streak_length(self) -> float:
        """Get average streak length."""
        result = await self.db.execute(
            select(func.avg(Streak.current_streak))
        )
        return result.scalar() or 0.0
    
    async def create(self, streak: Streak) -> Streak:
        """Create a new streak."""
        self.db.add(streak)
        await self.db.flush()
        await self.db.refresh(streak)
        return streak
    
    async def update(self, streak: Streak) -> Streak:
        """Update a streak."""
        await self.db.flush()
        await self.db.refresh(streak)
        return streak
    
    async def get_or_create(self, student_id: int, pdf_id: int) -> Streak:
        """Get existing streak or create new one."""
        streak = await self.get_student_streak(student_id, pdf_id)
        if streak is None:
            streak = Streak(student_id=student_id, pdf_id=pdf_id)
            streak = await self.create(streak)
        return streak


class StreakRecoveryRepository:
    """Repository for streak recovery request data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, request_id: int) -> StreakRecoveryRequest | None:
        """Get request by ID."""
        result = await self.db.execute(
            select(StreakRecoveryRequest).where(StreakRecoveryRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def get_pending_requests(self) -> list[StreakRecoveryRequest]:
        """Get all pending recovery requests."""
        result = await self.db.execute(
            select(StreakRecoveryRequest).where(
                StreakRecoveryRequest.status == RecoveryStatus.PENDING
            ).order_by(StreakRecoveryRequest.created_at)
        )
        return list(result.scalars().all())
    
    async def get_student_requests(self, student_id: int) -> list[StreakRecoveryRequest]:
        """Get all requests by a student."""
        result = await self.db.execute(
            select(StreakRecoveryRequest).where(
                StreakRecoveryRequest.student_id == student_id
            ).order_by(StreakRecoveryRequest.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def count_pending(self) -> int:
        """Count pending requests."""
        result = await self.db.execute(
            select(func.count(StreakRecoveryRequest.id)).where(
                StreakRecoveryRequest.status == RecoveryStatus.PENDING
            )
        )
        return result.scalar() or 0
    
    async def create(self, request: StreakRecoveryRequest) -> StreakRecoveryRequest:
        """Create a new recovery request."""
        self.db.add(request)
        await self.db.flush()
        await self.db.refresh(request)
        return request
    
    async def update(self, request: StreakRecoveryRequest) -> StreakRecoveryRequest:
        """Update a recovery request."""
        await self.db.flush()
        await self.db.refresh(request)
        return request
