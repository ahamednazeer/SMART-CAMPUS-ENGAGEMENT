import os
import aiofiles
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.core.config import settings
from app.repositories.pdf_repository import PDFRepository, PDFAssignmentRepository
from app.repositories.user_repository import UserRepository
from app.models.pdf import PDF, PDFAssignment
from app.models.user import UserRole
from app.schemas.pdf import (
    PDFCreate, PDFUpdate, PDFOut, PDFListOut,
    AssignmentCreate, AssignmentOut
)


class PDFService:
    """Service for PDF management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pdf_repo = PDFRepository(db)
        self.assignment_repo = PDFAssignmentRepository(db)
        self.user_repo = UserRepository(db)
    
    async def upload_pdf(
        self, file: UploadFile, data: PDFCreate, uploaded_by: int
    ) -> PDFOut:
        """Upload a PDF file and create record."""
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Generate unique filename
        timestamp = date.today().isoformat()
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create PDF record
        pdf = PDF(
            filename=file.filename,
            file_path=file_path,
            title=data.title,
            subject=data.subject,
            description=data.description,
            target_batch=data.target_batch,
            start_date=data.start_date,
            end_date=data.end_date,
            min_daily_reading_minutes=data.min_daily_reading_minutes,
            uploaded_by=uploaded_by,
        )
        
        pdf = await self.pdf_repo.create(pdf)
        return PDFOut.model_validate(pdf)
    
    async def get_pdf(self, pdf_id: int) -> PDFOut:
        """Get PDF by ID."""
        pdf = await self.pdf_repo.get_by_id(pdf_id)
        if pdf is None:
            raise ValueError("PDF not found")
        return PDFOut.model_validate(pdf)
    
    async def get_all_pdfs(self, skip: int = 0, limit: int = 100) -> PDFListOut:
        """Get all PDFs with pagination."""
        pdfs = await self.pdf_repo.get_all(skip, limit)
        return PDFListOut(
            pdfs=[PDFOut.model_validate(p) for p in pdfs],
            total=len(pdfs)
        )
    
    async def update_pdf(self, pdf_id: int, data: PDFUpdate) -> PDFOut:
        """Update a PDF."""
        pdf = await self.pdf_repo.get_by_id(pdf_id)
        if pdf is None:
            raise ValueError("PDF not found")
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pdf, field, value)
        
        pdf = await self.pdf_repo.update(pdf)
        return PDFOut.model_validate(pdf)
    
    async def publish_pdf(self, pdf_id: int) -> PDFOut:
        """Publish a PDF."""
        pdf = await self.pdf_repo.get_by_id(pdf_id)
        if pdf is None:
            raise ValueError("PDF not found")
        
        pdf.is_published = True
        pdf = await self.pdf_repo.update(pdf)
        return PDFOut.model_validate(pdf)
    
    async def delete_pdf(self, pdf_id: int) -> None:
        """Delete a PDF and its file."""
        pdf = await self.pdf_repo.get_by_id(pdf_id)
        if pdf is None:
            raise ValueError("PDF not found")
        
        # Delete file if exists
        if os.path.exists(pdf.file_path):
            os.remove(pdf.file_path)
        
        await self.pdf_repo.delete(pdf)
    
    async def assign_pdf(self, data: AssignmentCreate) -> list[AssignmentOut]:
        """Assign PDF to students."""
        pdf = await self.pdf_repo.get_by_id(data.pdf_id)
        if pdf is None:
            raise ValueError("PDF not found")
        
        student_ids = data.student_ids or []
        
        # If batch is specified, get all students in batch
        if data.batch:
            students = await self.user_repo.get_students_by_batch(data.batch)
            student_ids.extend([s.id for s in students])
        
        # Remove duplicates
        student_ids = list(set(student_ids))
        
        # Create assignments
        assignments = []
        for student_id in student_ids:
            # Check if assignment already exists
            existing = await self.assignment_repo.get_student_pdf_assignment(
                student_id, data.pdf_id
            )
            if existing:
                continue
            
            assignment = PDFAssignment(
                pdf_id=data.pdf_id,
                student_id=student_id,
            )
            assignments.append(assignment)
        
        if assignments:
            assignments = await self.assignment_repo.create_bulk(assignments)
        
        return [AssignmentOut.model_validate(a) for a in assignments]
    
    async def get_student_assignments(self, student_id: int) -> list[AssignmentOut]:
        """Get all PDF assignments for a student."""
        assignments = await self.assignment_repo.get_student_assignments(student_id)
        return [AssignmentOut.model_validate(a) for a in assignments]
