from datetime import date, datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reading import ReadingSession, DailyReadingLog


class ReadingSessionRepository:
    """Repository for reading session data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, session_id: int) -> ReadingSession | None:
        """Get session by ID."""
        result = await self.db.execute(
            select(ReadingSession).where(ReadingSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_session(self, student_id: int, pdf_id: int) -> ReadingSession | None:
        """Get active (non-completed) session for student and PDF.
        If multiple exist (error state), returns the most recent one.
        """
        result = await self.db.execute(
            select(ReadingSession).where(
                ReadingSession.student_id == student_id,
                ReadingSession.pdf_id == pdf_id,
                ReadingSession.is_completed == False,
                ReadingSession.session_date == date.today()
            ).order_by(ReadingSession.start_time.desc())
        )
        # Use first() instead of scalar_one_or_none() to survive duplicates
        return result.scalars().first()
    
    async def get_today_sessions(self, student_id: int, pdf_id: int) -> list[ReadingSession]:
        """Get all sessions for today."""
        result = await self.db.execute(
            select(ReadingSession).where(
                ReadingSession.student_id == student_id,
                ReadingSession.pdf_id == pdf_id,
                ReadingSession.session_date == date.today()
            ).order_by(ReadingSession.start_time)
        )
        return list(result.scalars().all())
    
    async def get_sessions_by_date(
        self, student_id: int, pdf_id: int, session_date: date
    ) -> list[ReadingSession]:
        """Get all sessions for a specific date."""
        result = await self.db.execute(
            select(ReadingSession).where(
                ReadingSession.student_id == student_id,
                ReadingSession.pdf_id == pdf_id,
                ReadingSession.session_date == session_date,
                ReadingSession.is_valid == True
            ).order_by(ReadingSession.start_time)
        )
        return list(result.scalars().all())
    
    async def get_today_total_seconds(self, student_id: int, pdf_id: int) -> int:
        """Get total valid reading seconds for today."""
        result = await self.db.execute(
            select(func.coalesce(func.sum(ReadingSession.valid_duration_seconds), 0)).where(
                ReadingSession.student_id == student_id,
                ReadingSession.pdf_id == pdf_id,
                ReadingSession.session_date == date.today(),
                ReadingSession.is_valid == True
            )
        )
        return result.scalar() or 0
    
    async def create(self, session: ReadingSession) -> ReadingSession:
        """Create a new reading session."""
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def update(self, session: ReadingSession) -> ReadingSession:
        """Update a reading session."""
        await self.db.flush()
        await self.db.refresh(session)
        return session


class DailyReadingLogRepository:
    """Repository for daily reading log data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, log_id: int) -> DailyReadingLog | None:
        """Get log by ID."""
        result = await self.db.execute(
            select(DailyReadingLog).where(DailyReadingLog.id == log_id)
        )
        return result.scalar_one_or_none()
    
    async def get_log(
        self, student_id: int, pdf_id: int, log_date: date
    ) -> DailyReadingLog | None:
        """Get daily log for specific date."""
        result = await self.db.execute(
            select(DailyReadingLog).where(
                DailyReadingLog.student_id == student_id,
                DailyReadingLog.pdf_id == pdf_id,
                DailyReadingLog.log_date == log_date
            )
        )
        return result.scalar_one_or_none()
    
    async def get_student_logs(
        self, student_id: int, pdf_id: int
    ) -> list[DailyReadingLog]:
        """Get all logs for a student and PDF."""
        result = await self.db.execute(
            select(DailyReadingLog).where(
                DailyReadingLog.student_id == student_id,
                DailyReadingLog.pdf_id == pdf_id
            ).order_by(DailyReadingLog.log_date)
        )
        return list(result.scalars().all())
    
    async def get_unlocked_logs(self, log_date: date) -> list[DailyReadingLog]:
        """Get all unlocked logs for a date (for daily evaluation)."""
        result = await self.db.execute(
            select(DailyReadingLog).where(
                DailyReadingLog.log_date == log_date,
                DailyReadingLog.is_locked == False
            )
        )
        return list(result.scalars().all())
    
    async def get_pending_logs_for_student(self, student_id: int) -> list[DailyReadingLog]:
        """Get all pending (unlocked) logs for a student prior to today."""
        result = await self.db.execute(
            select(DailyReadingLog).where(
                DailyReadingLog.student_id == student_id,
                DailyReadingLog.is_locked == False,
                DailyReadingLog.log_date < date.today()
            ).order_by(DailyReadingLog.log_date)
        )
        return list(result.scalars().all())

    async def create(self, log: DailyReadingLog) -> DailyReadingLog:
        """Create a new daily log."""
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log
    
    async def update(self, log: DailyReadingLog) -> DailyReadingLog:
        """Update a daily log."""
        await self.db.flush()
        await self.db.refresh(log)
        return log
    
    async def get_or_create(
        self, student_id: int, pdf_id: int, log_date: date
    ) -> DailyReadingLog:
        """Get existing log or create new one."""
        log = await self.get_log(student_id, pdf_id, log_date)
        if log is None:
            log = DailyReadingLog(
                student_id=student_id,
                pdf_id=pdf_id,
                log_date=log_date
            )
            log = await self.create(log)
        return log
