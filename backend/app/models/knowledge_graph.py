"""
Knowledge Graph models for visual learning maps.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DependencyStrength(str, enum.Enum):
    """Prerequisite dependency strength."""
    REQUIRED = "REQUIRED"  # Must complete before
    RECOMMENDED = "RECOMMENDED"  # Helpful but not required
    RELATED = "RELATED"  # Conceptually connected


class ProgressStatus(str, enum.Enum):
    """Student progress status on a topic."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class KnowledgeTopic(Base):
    """A topic node in the knowledge graph."""
    
    __tablename__ = "knowledge_topics"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Course/subject link
    course_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    
    # Semester for ordering
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Difficulty level (1-5)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Estimated hours to learn
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Keywords for linking
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)  # Comma-separated
    
    # External resources
    resources_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Graph positioning (for visualization)
    x_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    y_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    dependencies = relationship(
        "TopicDependency",
        foreign_keys="TopicDependency.topic_id",
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    prerequisite_for = relationship(
        "TopicDependency",
        foreign_keys="TopicDependency.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<KnowledgeTopic {self.name}>"


class TopicDependency(Base):
    """Prerequisite relationship between topics."""
    
    __tablename__ = "topic_dependencies"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # The topic that has a prerequisite
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_topics.id", ondelete="CASCADE"), index=True
    )
    
    # The prerequisite topic
    prerequisite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_topics.id", ondelete="CASCADE"), index=True
    )
    
    strength: Mapped[DependencyStrength] = mapped_column(
        Enum(DependencyStrength), default=DependencyStrength.RECOMMENDED
    )
    
    # Description of why this is a prerequisite
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    topic = relationship("KnowledgeTopic", foreign_keys=[topic_id], back_populates="dependencies")
    prerequisite = relationship("KnowledgeTopic", foreign_keys=[prerequisite_id], back_populates="prerequisite_for")
    
    def __repr__(self) -> str:
        return f"<TopicDependency {self.prerequisite_id} -> {self.topic_id}>"


class StudentTopicProgress(Base):
    """Student's progress on a knowledge topic."""
    
    __tablename__ = "student_topic_progress"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_topics.id", ondelete="CASCADE"), index=True
    )
    
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(ProgressStatus), default=ProgressStatus.NOT_STARTED
    )
    
    # Progress percentage (0-100)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    
    # Confidence score from quizzes/battles (0-100)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Time spent on this topic
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Last activity
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Quiz/flashcard attempts on this topic
    quiz_attempts: Mapped[int] = mapped_column(Integer, default=0)
    avg_quiz_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<StudentTopicProgress student={self.student_id} topic={self.topic_id}>"


class LearningPath(Base):
    """Curated learning path through topics."""
    
    __tablename__ = "learning_paths"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Target audience
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Estimated duration
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    topics = relationship("LearningPathTopic", back_populates="path", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<LearningPath {self.name}>"


class LearningPathTopic(Base):
    """Topic within a learning path with order."""
    
    __tablename__ = "learning_path_topics"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    path_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"), index=True
    )
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_topics.id", ondelete="CASCADE"), index=True
    )
    
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Optional notes for this topic in the path
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    path = relationship("LearningPath", back_populates="topics")
    
    def __repr__(self) -> str:
        return f"<LearningPathTopic path={self.path_id} topic={self.topic_id}>"
