"""
Flashcard Battle models for competitive micro-learning.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, JSON, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BattleType(str, enum.Enum):
    """Type of flashcard battle."""
    FRIEND = "FRIEND"  # Challenge a specific friend
    RANDOM = "RANDOM"  # Match with random classmate
    PUBLIC = "PUBLIC"  # Join public battle room


class BattleStatus(str, enum.Enum):
    """Battle status."""
    WAITING = "WAITING"  # Waiting for opponent
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FlashcardSet(Base):
    """Collection of flashcards for a topic."""
    
    __tablename__ = "flashcard_sets"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Topic/course link
    course_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Creator
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Visibility
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Stats
    total_cards: Mapped[int] = mapped_column(Integer, default=0)
    times_played: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    cards = relationship("Flashcard", back_populates="set", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<FlashcardSet {self.title}>"


class Flashcard(Base):
    """Individual flashcard with Q&A."""
    
    __tablename__ = "flashcards"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    set_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("flashcard_sets.id", ondelete="CASCADE"), index=True
    )
    
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # For multiple choice battles
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["Option A", "Option B", ...]
    correct_option: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-based index
    
    # Difficulty for adaptive learning
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    set = relationship("FlashcardSet", back_populates="cards")
    
    def __repr__(self) -> str:
        return f"<Flashcard set={self.set_id} order={self.order}>"


class FlashcardBattle(Base):
    """A flashcard battle session."""
    
    __tablename__ = "flashcard_battles"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    set_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("flashcard_sets.id", ondelete="CASCADE"), index=True
    )
    
    battle_type: Mapped[BattleType] = mapped_column(Enum(BattleType))
    status: Mapped[BattleStatus] = mapped_column(
        Enum(BattleStatus), default=BattleStatus.WAITING
    )
    
    # Game configuration
    num_questions: Mapped[int] = mapped_column(Integer, default=10)
    time_per_question: Mapped[int] = mapped_column(Integer, default=15)  # seconds
    
    # Question order (shuffled indices)
    question_order: Mapped[list | None] = mapped_column(JSON, nullable=True)
    current_question: Mapped[int] = mapped_column(Integer, default=0)
    
    # Creator (for friend/public battles)
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    participants = relationship("BattleParticipant", back_populates="battle", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<FlashcardBattle id={self.id} type={self.battle_type.value}>"


class BattleParticipant(Base):
    """Participant in a flashcard battle."""
    
    __tablename__ = "battle_participants"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    battle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("flashcard_battles.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    score: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_time_ms: Mapped[int] = mapped_column(Integer, default=0)  # Total response time
    
    # Answers (question_id -> answer)
    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    is_winner: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    battle = relationship("FlashcardBattle", back_populates="participants")
    
    def __repr__(self) -> str:
        return f"<BattleParticipant user={self.user_id} battle={self.battle_id}>"


class FlashcardLeaderboard(Base):
    """Periodic leaderboard for flashcard battles."""
    
    __tablename__ = "flashcard_leaderboard"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    # Period (weekly/monthly)
    period_type: Mapped[str] = mapped_column(String(20))  # "WEEKLY", "MONTHLY", "ALL_TIME"
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Stats
    total_battles: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<FlashcardLeaderboard user={self.user_id} rank={self.rank}>"
