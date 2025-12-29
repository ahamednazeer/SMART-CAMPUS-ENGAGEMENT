from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Quiz(Base):
    """Quiz model linked to PDF."""
    
    __tablename__ = "quizzes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    pdf_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pdfs.id", ondelete="CASCADE"), index=True
    )
    
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    # Day to unlock (1, 2, 3, etc. - relative to assignment start)
    day_unlock: Mapped[int] = mapped_column(Integer, default=1)
    
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Whether students can see correct answers after completing the quiz
    show_answers_after_completion: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Quiz {self.title}>"


class QuizQuestion(Base):
    """Quiz question with multiple choice options."""
    
    __tablename__ = "quiz_questions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    quiz_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    
    question_text: Mapped[str] = mapped_column(Text)
    
    # Options stored as JSON array: ["Option A", "Option B", "Option C", "Option D"]
    options: Mapped[list] = mapped_column(JSON)
    
    # Index of correct answer (0-based)
    correct_answer: Mapped[int] = mapped_column(Integer)
    
    # Display order
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    
    def __repr__(self) -> str:
        return f"<QuizQuestion quiz={self.quiz_id} order={self.order}>"


class QuizAttempt(Base):
    """Student quiz attempt and score."""
    
    __tablename__ = "quiz_attempts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    quiz_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    
    # Student's answers as JSON: {question_id: selected_option_index}
    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    score: Mapped[int] = mapped_column(Integer, default=0)  # Number of correct answers
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    def __repr__(self) -> str:
        return f"<QuizAttempt student={self.student_id} quiz={self.quiz_id} score={self.score}>"
