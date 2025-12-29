import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Notification type enumeration."""
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    STREAK = "STREAK"
    QUIZ = "QUIZ"
    ASSIGNMENT = "ASSIGNMENT"


class Notification(Base):
    """In-app notification model."""
    
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), default=NotificationType.INFO
    )
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Optional link to related resource
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    
    def __repr__(self) -> str:
        return f"<Notification {self.title} for user {self.user_id}>"
