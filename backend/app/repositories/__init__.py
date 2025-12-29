from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.repositories.pdf_repository import PDFRepository, PDFAssignmentRepository
from app.repositories.reading_repository import ReadingSessionRepository, DailyReadingLogRepository
from app.repositories.streak_repository import StreakRepository, StreakRecoveryRepository
from app.repositories.quiz_repository import QuizRepository, QuizQuestionRepository, QuizAttemptRepository
from app.repositories.audit_repository import AuditRepository

__all__ = [
    "UserRepository",
    "PDFRepository",
    "PDFAssignmentRepository",
    "ReadingSessionRepository",
    "DailyReadingLogRepository",
    "StreakRepository",
    "StreakRecoveryRepository",
    "QuizRepository",
    "QuizQuestionRepository",
    "QuizAttemptRepository",
    "AuditRepository",
]
