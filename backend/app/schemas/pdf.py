from datetime import datetime, date
from pydantic import BaseModel


class PDFBase(BaseModel):
    """Base PDF schema."""
    title: str
    subject: str | None = None
    description: str | None = None
    target_batch: str | None = None
    start_date: date
    end_date: date
    min_daily_reading_minutes: int = 5


class PDFCreate(PDFBase):
    """PDF creation schema."""
    pass


class PDFUpdate(BaseModel):
    """PDF update schema."""
    title: str | None = None
    subject: str | None = None
    description: str | None = None
    target_batch: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    min_daily_reading_minutes: int | None = None
    is_published: bool | None = None


class PDFOut(PDFBase):
    """PDF output schema."""
    id: int
    filename: str
    file_path: str
    is_published: bool
    uploaded_by: int | None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PDFListOut(BaseModel):
    """List of PDFs output schema."""
    pdfs: list[PDFOut]
    total: int


class AssignmentCreate(BaseModel):
    """PDF assignment creation schema."""
    pdf_id: int
    student_ids: list[int] | None = None  # If None, assign to all in batch
    batch: str | None = None  # Assign to all students in batch


class AssignmentOut(BaseModel):
    """Assignment output schema."""
    id: int
    pdf_id: int
    student_id: int
    is_active: bool
    assigned_at: datetime
    
    class Config:
        from_attributes = True


class StudentPDFOut(BaseModel):
    """PDF with assignment info for student view."""
    pdf: PDFOut
    assignment_id: int
    assigned_at: datetime
    reading_progress: int = 0  # Total reading time in seconds
    is_completed: bool = False  # Met minimum reading time
