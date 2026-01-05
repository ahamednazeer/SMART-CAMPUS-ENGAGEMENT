"""
Course Review models for anonymous moderated feedback.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ReviewStatus(str, enum.Enum):
    """Review moderation status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewWindow(Base):
    """Time-bound period for submitting course reviews."""
    
    __tablename__ = "review_windows"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100))  # e.g., "Fall 2024 End-of-Semester"
    
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Optional: limit to specific courses/semesters
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<ReviewWindow {self.name}>"


class CourseReview(Base):
    """Student review of a course - anonymous to faculty."""
    
    __tablename__ = "course_reviews"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    
    # Student identity - known only to system, never exposed to faculty
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    # Review window (optional)
    window_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("review_windows.id", ondelete="SET NULL"), nullable=True
    )
    
    # Ratings (1-5 scale)
    difficulty_rating: Mapped[int] = mapped_column(Integer)  # 1=Easy, 5=Very Hard
    clarity_rating: Mapped[int] = mapped_column(Integer)  # Teaching clarity
    relevance_rating: Mapped[int] = mapped_column(Integer)  # Content relevance
    overall_rating: Mapped[int] = mapped_column(Integer)  # Overall satisfaction
    
    # Optional text feedback
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Moderation
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.PENDING
    )
    
    # Moderation details
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False)
    moderated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Flags for inappropriate content
    has_personal_attack: Mapped[bool] = mapped_column(Boolean, default=False)
    has_abusive_content: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<CourseReview course={self.course_id} overall={self.overall_rating}>"


class CourseReviewAggregate(Base):
    """Aggregated review statistics for a course - publicly visible."""
    
    __tablename__ = "course_review_aggregates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), unique=True, index=True
    )
    
    # Aggregate ratings
    avg_difficulty: Mapped[float] = mapped_column(Integer, default=0)
    avg_clarity: Mapped[float] = mapped_column(Integer, default=0)
    avg_relevance: Mapped[float] = mapped_column(Integer, default=0)
    avg_overall: Mapped[float] = mapped_column(Integer, default=0)
    
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    
    # Last updated
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<CourseReviewAggregate course={self.course_id} avg={self.avg_overall}>"
