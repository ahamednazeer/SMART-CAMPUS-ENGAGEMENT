from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.quiz_repository import QuizRepository, QuizQuestionRepository, QuizAttemptRepository
from app.repositories.pdf_repository import PDFAssignmentRepository
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizOut, QuizFullOut, QuizStudentOut,
    QuestionCreate, QuestionFullOut, QuestionOut,
    AttemptSubmit, AttemptOut, AttemptResultOut
)


class QuizService:
    """Service for quiz management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.quiz_repo = QuizRepository(db)
        self.question_repo = QuizQuestionRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)
        self.assignment_repo = PDFAssignmentRepository(db)
    
    async def create_quiz(self, data: QuizCreate, created_by: int) -> QuizFullOut:
        """Create a new quiz with questions."""
        quiz = Quiz(
            pdf_id=data.pdf_id,
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            day_unlock=data.day_unlock,
            total_questions=len(data.questions),
            created_by=created_by,
        )
        
        quiz = await self.quiz_repo.create(quiz)
        
        # Create questions
        questions = []
        for i, q_data in enumerate(data.questions):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data.question_text,
                options=q_data.options,
                correct_answer=q_data.correct_answer,
                order=q_data.order or i,
            )
            questions.append(question)
        
        if questions:
            await self.question_repo.create_bulk(questions)
        
        return await self.get_quiz_full(quiz.id)
    
    async def get_quiz(self, quiz_id: int) -> QuizOut:
        """Get quiz by ID."""
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        return QuizOut.model_validate(quiz)
    
    async def get_quiz_full(self, quiz_id: int) -> QuizFullOut:
        """Get quiz with questions (admin view)."""
        quiz = await self.quiz_repo.get_with_questions(quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        
        return QuizFullOut(
            id=quiz.id,
            pdf_id=quiz.pdf_id,
            title=quiz.title,
            description=quiz.description,
            total_questions=quiz.total_questions,
            duration_minutes=quiz.duration_minutes,
            day_unlock=quiz.day_unlock,
            is_published=quiz.is_published,
            created_at=quiz.created_at,
            questions=[QuestionFullOut.model_validate(q) for q in quiz.questions],
        )
    
    async def get_quiz_for_student(
        self, quiz_id: int, student_id: int
    ) -> QuizStudentOut:
        """Get quiz for student (without correct answers)."""
        quiz = await self.quiz_repo.get_with_questions(quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        
        if not quiz.is_published:
            raise ValueError("Quiz is not available")
        
        # Check if already attempted
        attempt = await self.attempt_repo.get_student_attempt(student_id, quiz_id)
        
        return QuizStudentOut(
            id=quiz.id,
            pdf_id=quiz.pdf_id,
            title=quiz.title,
            description=quiz.description,
            total_questions=quiz.total_questions,
            duration_minutes=quiz.duration_minutes,
            day_unlock=quiz.day_unlock,
            is_published=quiz.is_published,
            created_at=quiz.created_at,
            questions=[QuestionOut.model_validate(q) for q in quiz.questions],
            is_attempted=attempt is not None and attempt.is_completed,
            attempt_score=attempt.score if attempt and attempt.is_completed else None,
        )
    
    async def update_quiz(self, quiz_id: int, data: QuizUpdate) -> QuizOut:
        """Update a quiz."""
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        
        if quiz.is_published and data.is_published is not False:
            # Only allow unpublishing for published quizzes
            raise ValueError("Cannot edit published quiz")
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(quiz, field, value)
        
        quiz = await self.quiz_repo.update(quiz)
        return QuizOut.model_validate(quiz)
    
    async def publish_quiz(self, quiz_id: int) -> QuizOut:
        """Publish a quiz."""
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        
        quiz.is_published = True
        quiz = await self.quiz_repo.update(quiz)
        return QuizOut.model_validate(quiz)
    
    async def delete_quiz(self, quiz_id: int) -> None:
        """Delete a quiz."""
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        
        if quiz.is_published:
            raise ValueError("Cannot delete published quiz")
        
        await self.quiz_repo.delete(quiz)
    
    async def get_pdf_quizzes(self, pdf_id: int) -> list[QuizOut]:
        """Get all quizzes for a PDF."""
        quizzes = await self.quiz_repo.get_by_pdf(pdf_id)
        return [QuizOut.model_validate(q) for q in quizzes]
    
    async def start_attempt(self, student_id: int, quiz_id: int) -> AttemptOut:
        """Start a quiz attempt."""
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        
        if not quiz.is_published:
            raise ValueError("Quiz is not available")
        
        # Check for existing attempt
        existing = await self.attempt_repo.get_student_attempt(student_id, quiz_id)
        if existing:
            if existing.is_completed:
                raise ValueError("Quiz already completed")
            return AttemptOut.model_validate(existing)
        
        attempt = QuizAttempt(
            student_id=student_id,
            quiz_id=quiz_id,
            total_questions=quiz.total_questions,
        )
        
        attempt = await self.attempt_repo.create(attempt)
        return AttemptOut.model_validate(attempt)
    
    async def submit_attempt(
        self, student_id: int, data: AttemptSubmit
    ) -> AttemptResultOut:
        """Submit quiz answers and calculate score."""
        attempt = await self.attempt_repo.get_student_attempt(student_id, data.quiz_id)
        if attempt is None:
            raise ValueError("No active attempt found")
        
        if attempt.is_completed:
            raise ValueError("Quiz already submitted")
        
        # Get quiz to check show_answers setting
        quiz = await self.quiz_repo.get_by_id(data.quiz_id)
        if quiz is None:
            raise ValueError("Quiz not found")
        
        # Get questions
        questions = await self.question_repo.get_quiz_questions(data.quiz_id)
        question_map = {str(q.id): q for q in questions}
        
        # Calculate score
        score = 0
        correct_answers = {}
        
        for q in questions:
            correct_answers[str(q.id)] = q.correct_answer
            if str(q.id) in data.answers:
                if data.answers[str(q.id)] == q.correct_answer:
                    score += 1
        
        # Update attempt
        attempt.answers = data.answers
        attempt.score = score
        attempt.submitted_at = datetime.now(timezone.utc)
        attempt.is_completed = True
        
        attempt = await self.attempt_repo.update(attempt)
        
        # Only include correct_answers if quiz allows it
        show_answers = quiz.show_answers_after_completion
        
        return AttemptResultOut(
            id=attempt.id,
            student_id=attempt.student_id,
            quiz_id=attempt.quiz_id,
            score=attempt.score,
            total_questions=attempt.total_questions,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            is_completed=attempt.is_completed,
            answers=attempt.answers,
            correct_answers=correct_answers if show_answers else None,
            show_answers=show_answers,
        )
    
    async def get_student_attempts(self, student_id: int) -> list[AttemptOut]:
        """Get all quiz attempts by a student."""
        attempts = await self.attempt_repo.get_student_attempts(student_id)
        return [AttemptOut.model_validate(a) for a in attempts]
    
    async def get_all_attempts(self) -> list[AttemptOut]:
        """Get all quiz attempts (for admin)."""
        attempts = await self.attempt_repo.get_all_attempts(completed_only=True)
        return [AttemptOut.model_validate(a) for a in attempts]
    
    async def get_quiz_attempts(self, quiz_id: int) -> list[AttemptOut]:
        """Get all attempts for a specific quiz (for admin)."""
        attempts = await self.attempt_repo.get_quiz_attempts(quiz_id, completed_only=True)
        return [AttemptOut.model_validate(a) for a in attempts]
