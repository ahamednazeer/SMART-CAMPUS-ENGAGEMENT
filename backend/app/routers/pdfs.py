from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
import json
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.pdf_service import PDFService
from app.services.audit_service import AuditService
from app.schemas.pdf import (
    PDFCreate, PDFUpdate, PDFOut, PDFListOut,
    AssignmentCreate, AssignmentOut
)

router = APIRouter(prefix="/pdfs", tags=["PDFs"])


@router.get("", response_model=PDFListOut)
async def get_pdfs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100
):
    """Get all PDFs (admin only)."""
    service = PDFService(db)
    return await service.get_all_pdfs(skip, limit)


@router.post("", response_model=PDFOut, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    start_date: Annotated[str, Form()],
    end_date: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    subject: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    target_batch: Annotated[str | None, Form()] = None,
    min_daily_reading_minutes: Annotated[int, Form()] = 5,
):
    """Upload a new PDF (admin only)."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    data = PDFCreate(
        title=title,
        subject=subject,
        description=description,
        target_batch=target_batch,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        min_daily_reading_minutes=min_daily_reading_minutes,
    )
    
    service = PDFService(db)
    audit = AuditService(db)
    pdf = await service.upload_pdf(file, data, current_user.id)
    await audit.log_action(
        user_id=current_user.id,
        action="UPLOAD",
        resource_type="pdf",
        resource_id=pdf.id,
        details={"title": pdf.title, "filename": file.filename}
    )
    return pdf


@router.get("/{pdf_id}", response_model=PDFOut)
async def get_pdf(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)]
):
    """Get PDF by ID."""
    service = PDFService(db)
    try:
        return await service.get_pdf(pdf_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{pdf_id}", response_model=PDFOut)
async def update_pdf(
    pdf_id: int,
    data: PDFUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Update a PDF (admin only)."""
    service = PDFService(db)
    try:
        return await service.update_pdf(pdf_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{pdf_id}/publish", response_model=PDFOut)
async def publish_pdf(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Publish a PDF (admin only)."""
    service = PDFService(db)
    try:
        return await service.publish_pdf(pdf_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Delete a PDF (admin only)."""
    service = PDFService(db)
    audit = AuditService(db)
    try:
        await service.delete_pdf(pdf_id)
        await audit.log_action(
            user_id=admin.id,
            action="DELETE",
            resource_type="pdf",
            resource_id=pdf_id,
            details={"deleted_pdf_id": pdf_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{pdf_id}/download")
async def download_pdf(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)]
):
    """Download a PDF file."""
    service = PDFService(db)
    try:
        pdf = await service.get_pdf(pdf_id)
        return FileResponse(
            pdf.file_path,
            media_type="application/pdf",
            filename=pdf.filename
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{pdf_id}/assign", response_model=list[AssignmentOut])
async def assign_pdf(
    pdf_id: int,
    data: AssignmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Assign PDF to students (admin only)."""
    data.pdf_id = pdf_id
    service = PDFService(db)
    try:
        return await service.assign_pdf(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/student/assignments", response_model=list[AssignmentOut])
async def get_my_assignments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current student's PDF assignments."""
    service = PDFService(db)
    return await service.get_student_assignments(current_user.id)
