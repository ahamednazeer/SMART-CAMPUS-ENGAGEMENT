from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt


class QuizRepository:
    """Repository for quiz data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, quiz_id: int) -> Quiz | None:
        """Get quiz by ID."""
        result = await self.db.execute(select(Quiz).where(Quiz.id == quiz_id))
        return result.scalar_one_or_none()
    
    async def get_with_questions(self, quiz_id: int) -> Quiz | None:
        """Get quiz with questions loaded."""
        result = await self.db.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_pdf(self, pdf_id: int) -> list[Quiz]:
        """Get all quizzes for a PDF."""
        result = await self.db.execute(
            select(Quiz).where(Quiz.pdf_id == pdf_id).order_by(Quiz.day_unlock)
        )
        return list(result.scalars().all())
    
    async def get_published_by_pdf(self, pdf_id: int) -> list[Quiz]:
        """Get published quizzes for a PDF."""
        result = await self.db.execute(
            select(Quiz).where(
                Quiz.pdf_id == pdf_id,
                Quiz.is_published == True
            ).order_by(Quiz.day_unlock)
        )
        return list(result.scalars().all())
    
    async def create(self, quiz: Quiz) -> Quiz:
        """Create a new quiz."""
        self.db.add(quiz)
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def update(self, quiz: Quiz) -> Quiz:
        """Update a quiz."""
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz
    
    async def delete(self, quiz: Quiz) -> None:
        """Delete a quiz."""
        await self.db.delete(quiz)
        await self.db.flush()


class QuizQuestionRepository:
    """Repository for quiz question data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, question_id: int) -> QuizQuestion | None:
        """Get question by ID."""
        result = await self.db.execute(
            select(QuizQuestion).where(QuizQuestion.id == question_id)
        )
        return result.scalar_one_or_none()
    
    async def get_quiz_questions(self, quiz_id: int) -> list[QuizQuestion]:
        """Get all questions for a quiz."""
        result = await self.db.execute(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order)
        )
        return list(result.scalars().all())
    
    async def create(self, question: QuizQuestion) -> QuizQuestion:
        """Create a new question."""
        self.db.add(question)
        await self.db.flush()
        await self.db.refresh(question)
        return question
    
    async def create_bulk(self, questions: list[QuizQuestion]) -> list[QuizQuestion]:
        """Create multiple questions."""
        self.db.add_all(questions)
        await self.db.flush()
        return questions
    
    async def delete_quiz_questions(self, quiz_id: int) -> None:
        """Delete all questions for a quiz."""
        result = await self.db.execute(
            select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
        )
        questions = result.scalars().all()
        for q in questions:
            await self.db.delete(q)
        await self.db.flush()


class QuizAttemptRepository:
    """Repository for quiz attempt data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, attempt_id: int) -> QuizAttempt | None:
        """Get attempt by ID."""
        result = await self.db.execute(
            select(QuizAttempt).where(QuizAttempt.id == attempt_id)
        )
        return result.scalar_one_or_none()
    
    async def get_student_attempt(self, student_id: int, quiz_id: int) -> QuizAttempt | None:
        """Get a student's attempt for a quiz."""
        result = await self.db.execute(
            select(QuizAttempt).where(
                QuizAttempt.student_id == student_id,
                QuizAttempt.quiz_id == quiz_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_student_attempts(self, student_id: int) -> list[QuizAttempt]:
        """Get all attempts by a student."""
        result = await self.db.execute(
            select(QuizAttempt).where(
                QuizAttempt.student_id == student_id
            ).order_by(QuizAttempt.started_at.desc())
        )
        return list(result.scalars().all())
    
    async def create(self, attempt: QuizAttempt) -> QuizAttempt:
        """Create a new attempt."""
        self.db.add(attempt)
        await self.db.flush()
        await self.db.refresh(attempt)
        return attempt
    
    async def update(self, attempt: QuizAttempt) -> QuizAttempt:
        """Update an attempt."""
        await self.db.flush()
        await self.db.refresh(attempt)
        return attempt
    
    async def get_all_attempts(self, completed_only: bool = True) -> list[QuizAttempt]:
        """Get all quiz attempts (for admin)."""
        query = select(QuizAttempt)
        if completed_only:
            query = query.where(QuizAttempt.is_completed == True)
        query = query.order_by(QuizAttempt.submitted_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_quiz_attempts(self, quiz_id: int, completed_only: bool = True) -> list[QuizAttempt]:
        """Get all attempts for a specific quiz."""
        query = select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id)
        if completed_only:
            query = query.where(QuizAttempt.is_completed == True)
        query = query.order_by(QuizAttempt.submitted_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
