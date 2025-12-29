from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pdf import PDF, PDFAssignment


class PDFRepository:
    """Repository for PDF data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, pdf_id: int) -> PDF | None:
        """Get PDF by ID."""
        result = await self.db.execute(select(PDF).where(PDF.id == pdf_id))
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[PDF]:
        """Get all PDFs with pagination."""
        result = await self.db.execute(
            select(PDF).offset(skip).limit(limit).order_by(PDF.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_published(self) -> list[PDF]:
        """Get all published PDFs."""
        result = await self.db.execute(
            select(PDF).where(PDF.is_published == True).order_by(PDF.start_date)
        )
        return list(result.scalars().all())
    
    async def get_active(self, current_date: date | None = None) -> list[PDF]:
        """Get active PDFs (within date range)."""
        if current_date is None:
            current_date = date.today()
        
        result = await self.db.execute(
            select(PDF).where(
                PDF.is_published == True,
                PDF.start_date <= current_date,
                PDF.end_date >= current_date
            ).order_by(PDF.start_date)
        )
        return list(result.scalars().all())
    
    async def create(self, pdf: PDF) -> PDF:
        """Create a new PDF."""
        self.db.add(pdf)
        await self.db.flush()
        await self.db.refresh(pdf)
        return pdf
    
    async def update(self, pdf: PDF) -> PDF:
        """Update an existing PDF."""
        await self.db.flush()
        await self.db.refresh(pdf)
        return pdf
    
    async def delete(self, pdf: PDF) -> None:
        """Delete a PDF."""
        await self.db.delete(pdf)
        await self.db.flush()


class PDFAssignmentRepository:
    """Repository for PDF assignment data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, assignment_id: int) -> PDFAssignment | None:
        """Get assignment by ID."""
        result = await self.db.execute(
            select(PDFAssignment).where(PDFAssignment.id == assignment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_student_assignments(self, student_id: int) -> list[PDFAssignment]:
        """Get all active assignments for a student."""
        result = await self.db.execute(
            select(PDFAssignment).where(
                PDFAssignment.student_id == student_id,
                PDFAssignment.is_active == True
            ).order_by(PDFAssignment.assigned_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_student_pdf_assignment(self, student_id: int, pdf_id: int) -> PDFAssignment | None:
        """Get a specific student's assignment for a PDF."""
        result = await self.db.execute(
            select(PDFAssignment).where(
                PDFAssignment.student_id == student_id,
                PDFAssignment.pdf_id == pdf_id,
                PDFAssignment.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_pdf_assignments(self, pdf_id: int) -> list[PDFAssignment]:
        """Get all assignments for a PDF."""
        result = await self.db.execute(
            select(PDFAssignment).where(
                PDFAssignment.pdf_id == pdf_id,
                PDFAssignment.is_active == True
            )
        )
        return list(result.scalars().all())
    
    async def create(self, assignment: PDFAssignment) -> PDFAssignment:
        """Create a new assignment."""
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment
    
    async def create_bulk(self, assignments: list[PDFAssignment]) -> list[PDFAssignment]:
        """Create multiple assignments."""
        self.db.add_all(assignments)
        await self.db.flush()
        for assignment in assignments:
            await self.db.refresh(assignment)
        return assignments
