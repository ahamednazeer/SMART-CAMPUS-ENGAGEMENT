from datetime import datetime
from pydantic import BaseModel


class QuestionCreate(BaseModel):
    """Quiz question creation schema."""
    question_text: str
    options: list[str]  # ["Option A", "Option B", "Option C", "Option D"]
    correct_answer: int  # Index of correct option (0-based)
    order: int = 0


class QuestionOut(BaseModel):
    """Quiz question output schema (without correct answer for students)."""
    id: int
    question_text: str
    options: list[str]
    order: int
    
    class Config:
        from_attributes = True


class QuestionFullOut(QuestionOut):
    """Quiz question with correct answer (for admin)."""
    correct_answer: int


class QuizCreate(BaseModel):
    """Quiz creation schema."""
    pdf_id: int
    title: str
    description: str | None = None
    duration_minutes: int = 30
    day_unlock: int = 1
    show_answers_after_completion: bool = False
    questions: list[QuestionCreate] = []


class QuizUpdate(BaseModel):
    """Quiz update schema."""
    title: str | None = None
    description: str | None = None
    duration_minutes: int | None = None
    day_unlock: int | None = None
    is_published: bool | None = None
    show_answers_after_completion: bool | None = None


class QuizOut(BaseModel):
    """Quiz output schema."""
    id: int
    pdf_id: int
    title: str
    description: str | None
    total_questions: int
    duration_minutes: int
    day_unlock: int
    is_published: bool
    show_answers_after_completion: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuizFullOut(QuizOut):
    """Quiz with questions (for admin)."""
    questions: list[QuestionFullOut]


class QuizStudentOut(QuizOut):
    """Quiz for student view (without correct answers)."""
    questions: list[QuestionOut]
    is_attempted: bool = False
    attempt_score: int | None = None


class AttemptSubmit(BaseModel):
    """Quiz attempt submission."""
    quiz_id: int
    answers: dict[str, int]  # {question_id: selected_option_index}


class AttemptOut(BaseModel):
    """Quiz attempt output schema."""
    id: int
    student_id: int
    quiz_id: int
    score: int
    total_questions: int
    started_at: datetime
    submitted_at: datetime | None
    is_completed: bool
    
    class Config:
        from_attributes = True


class AttemptResultOut(AttemptOut):
    """Quiz attempt with detailed results."""
    answers: dict[str, int]
    correct_answers: dict[str, int] | None = None  # Only included if quiz allows showing answers
    show_answers: bool = False  # Flag to indicate if answers are available
