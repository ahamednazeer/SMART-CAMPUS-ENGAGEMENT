"""
Course and Subject models for academic structure.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CourseSemester(str, enum.Enum):
    """Semester enumeration."""
    SEM_1 = "SEM_1"
    SEM_2 = "SEM_2"
    SEM_3 = "SEM_3"
    SEM_4 = "SEM_4"
    SEM_5 = "SEM_5"
    SEM_6 = "SEM_6"
    SEM_7 = "SEM_7"
    SEM_8 = "SEM_8"


class Course(Base):
    """Course model representing an academic course."""
    
    __tablename__ = "courses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # e.g., "CS201"
    name: Mapped[str] = mapped_column(String(255))  # e.g., "Data Structures"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-8
    credits: Mapped[int] = mapped_column(Integer, default=3)
    
    faculty_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<Course {self.code}: {self.name}>"


class CourseEnrollment(Base):
    """Student enrollment in a course."""
    
    __tablename__ = "course_enrollments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g., "2024-25"
    
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<CourseEnrollment student={self.student_id} course={self.course_id}>"
