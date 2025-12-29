import enum
from datetime import datetime
from sqlalchemy import String, Boolean, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "ADMIN"
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    WARDEN = "WARDEN"
    MAINTENANCE_STAFF = "MAINTENANCE_STAFF"
    HOSTELLER = "HOSTELLER"
    DAY_SCHOLAR = "DAY_SCHOLAR"


class StudentCategory(str, enum.Enum):
    """Student category for streak rules."""
    HOSTELLER = "HOSTELLER"
    DAY_SCHOLAR = "DAY_SCHOLAR"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT)
    student_category: Mapped[StudentCategory | None] = mapped_column(
        Enum(StudentCategory), nullable=True
    )
    
    # Student-specific fields
    register_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    batch: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g., "2024"
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
