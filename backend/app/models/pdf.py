from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, Text, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PDF(Base):
    """PDF document model for reading materials."""
    
    __tablename__ = "pdfs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    filename: Mapped[str] = mapped_column(String(255))  # Original filename
    file_path: Mapped[str] = mapped_column(String(500))  # Storage path
    
    title: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    target_batch: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "2024"
    
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    
    min_daily_reading_minutes: Mapped[int] = mapped_column(Integer, default=5)
    
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    
    uploaded_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    assignments = relationship("PDFAssignment", back_populates="pdf", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<PDF {self.title}>"


class PDFAssignment(Base):
    """Assignment of PDF to student."""
    
    __tablename__ = "pdf_assignments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    pdf_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pdfs.id", ondelete="CASCADE"), index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    pdf = relationship("PDF", back_populates="assignments")
    
    def __repr__(self) -> str:
        return f"<PDFAssignment pdf={self.pdf_id} student={self.student_id}>"
