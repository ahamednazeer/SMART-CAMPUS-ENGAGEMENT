from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.reading_repository import ReadingSessionRepository, DailyReadingLogRepository
from app.repositories.pdf_repository import PDFRepository, PDFAssignmentRepository
from app.models.reading import ReadingSession, DailyReadingLog
from app.schemas.reading import (
    SessionStart, SessionOut, ReadingProgressOut, ReadingHistoryOut, DailyLogOut
)


class ReadingService:
    """Service for reading session management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = ReadingSessionRepository(db)
        self.log_repo = DailyReadingLogRepository(db)
        self.pdf_repo = PDFRepository(db)
        self.assignment_repo = PDFAssignmentRepository(db)
    
    async def start_session(self, student_id: int, data: SessionStart) -> SessionOut:
        """Start a new reading session."""
        # Verify assignment exists
        assignment = await self.assignment_repo.get_student_pdf_assignment(
            student_id, data.pdf_id
        )
        if not assignment:
            raise ValueError("PDF not assigned to student")
        
        # Check for existing active session
        existing = await self.session_repo.get_active_session(student_id, data.pdf_id)
        if existing:
            # Requirement 8: "Each open -> new session"
            existing.status = "completed"
            existing.end_time = datetime.now(timezone.utc)
            await self.session_repo.update(existing)
        
        # Create new session
        session = ReadingSession(
            student_id=student_id,
            pdf_id=data.pdf_id,
            session_date=date.today(),
            start_time=datetime.now(timezone.utc),
            status="active",
            pause_events=[],
            resume_events=[],
        )
        
        session = await self.session_repo.create(session)
        
        # Ensure daily log exists
        await self.log_repo.get_or_create(student_id, data.pdf_id, date.today())
        
        return SessionOut.model_validate(session)
    
    async def pause_session(self, student_id: int, session_id: int) -> SessionOut:
        """Pause a reading session."""
        session = await self.session_repo.get_by_id(session_id)
        if session is None or session.student_id != student_id:
            raise ValueError("Session not found")
        
        if session.status != "active":
            raise ValueError("Session is not active")
        
        now = datetime.now(timezone.utc)
        
        # Note: We do NOT add duration here because heartbeats already increment 
        # valid_duration_seconds. Adding here would double-count the time.
        # The heartbeat mechanism is the source of truth for valid reading time.
        
        # Record pause event
        if session.pause_events is None:
            session.pause_events = []
        session.pause_events.append(now.isoformat())
        session.status = "paused"
        
        session = await self.session_repo.update(session)
        return SessionOut.model_validate(session)
    
    async def resume_session(self, student_id: int, session_id: int) -> SessionOut:
        """Resume a paused reading session."""
        session = await self.session_repo.get_by_id(session_id)
        if session is None or session.student_id != student_id:
            raise ValueError("Session not found")
        
        if session.status != "paused":
            raise ValueError("Session is not paused")
        
        now = datetime.now(timezone.utc)
        
        # Record resume event
        if session.resume_events is None:
            session.resume_events = []
        session.resume_events.append(now.isoformat())
        session.status = "active"
        
        session = await self.session_repo.update(session)
        return SessionOut.model_validate(session)

    async def heartbeat_session(self, student_id: int, session_id: int, delta_seconds: int) -> SessionOut:
        """Update session activity via heartbeat."""
        if delta_seconds <= 0 or delta_seconds > 65:  # Allow 5s buffer
            raise ValueError("Invalid heartbeat delta")
        
        session = await self.session_repo.get_by_id(session_id)
        if session is None or session.student_id != student_id:
            raise ValueError("Session not found")
        
        if session.status != "active":
            # If paused/completed, ignore heartbeat or error.
            # Client might race, so just return current state
            return SessionOut.model_validate(session)
        
        session.valid_duration_seconds += delta_seconds
        
        session = await self.session_repo.update(session)
        
        # Update daily log periodically (or every heartbeat if load allows - usually safer to do it here)
        await self._update_daily_log(student_id, session.pdf_id, session.session_date)
        
        return SessionOut.model_validate(session)
    
    async def end_session(self, student_id: int, session_id: int, final_delta: int = 0) -> SessionOut:
        """End a reading session and update daily log."""
        session = await self.session_repo.get_by_id(session_id)
        if session is None or session.student_id != student_id:
            raise ValueError("Session not found")
        
        if session.is_completed:
            return SessionOut.model_validate(session)
        
        now = datetime.now(timezone.utc)
        
        # If session is active, apply the final delta provided by the client
        # This is more accurate than server-side calculation which might include "background" time
        # if the client doesn't explicitly pause before end.
        if session.status == "active":
             # Cap final_delta to prevent abuse (max 65s like heartbeat)
             # This ensures someone can't add arbitrary large time when they close the PDF
             if final_delta > 0 and final_delta <= 65:
                 session.valid_duration_seconds += final_delta
        
        session.end_time = now
        session.status = "completed"
        session.is_completed = True
        
        session = await self.session_repo.update(session)
        
        # Update daily log
        await self._update_daily_log(student_id, session.pdf_id, session.session_date)
        
        return SessionOut.model_validate(session)
    
    async def _update_daily_log(
        self, student_id: int, pdf_id: int, log_date: date
    ) -> DailyReadingLog:
        """Update daily log with total reading time."""
        log = await self.log_repo.get_or_create(student_id, pdf_id, log_date)
        
        # Calculate total from all valid sessions
        sessions = await self.session_repo.get_sessions_by_date(student_id, pdf_id, log_date)
        total_seconds = sum(s.valid_duration_seconds for s in sessions)
        
        log.total_valid_seconds = total_seconds
        
        # Get PDF to check minimum requirement
        pdf = await self.pdf_repo.get_by_id(pdf_id)
        if pdf:
            required_seconds = pdf.min_daily_reading_minutes * 60
            log.is_success = total_seconds >= required_seconds
        
        return await self.log_repo.update(log)
    
    async def get_reading_progress(
        self, student_id: int, pdf_id: int
    ) -> ReadingProgressOut:
        """Get student's reading progress for a PDF."""
        pdf = await self.pdf_repo.get_by_id(pdf_id)
        if pdf is None:
            raise ValueError("PDF not found")
        
        today_seconds = await self.session_repo.get_today_total_seconds(student_id, pdf_id)
        
        # Get total from all logs
        logs = await self.log_repo.get_student_logs(student_id, pdf_id)
        total_seconds = sum(log.total_valid_seconds for log in logs)
        
        required_seconds = pdf.min_daily_reading_minutes * 60
        
        # Check for active session
        active_session = await self.session_repo.get_active_session(student_id, pdf_id)
        
        return ReadingProgressOut(
            pdf_id=pdf_id,
            today_reading_seconds=today_seconds,
            total_reading_seconds=total_seconds,
            today_required_seconds=required_seconds,
            today_completed=today_seconds >= required_seconds,
            active_session=SessionOut.model_validate(active_session) if active_session else None,
        )
    
    async def get_reading_history(
        self, student_id: int, pdf_id: int
    ) -> ReadingHistoryOut:
        """Get student's reading history for a PDF."""
        logs = await self.log_repo.get_student_logs(student_id, pdf_id)
        
        return ReadingHistoryOut(
            daily_logs=[DailyLogOut.model_validate(log) for log in logs],
            total_days=len(logs),
            successful_days=sum(1 for log in logs if log.is_success),
        )
