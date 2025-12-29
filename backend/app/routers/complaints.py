"""Router for Maintenance Complaints."""
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User, UserRole
from app.services.complaint_service import ComplaintService
from app.models.complaint import ComplaintCategory, ComplaintStatus, ComplaintPriority

router = APIRouter(prefix="/complaints", tags=["Maintenance Complaints"])


# Schemas
class ComplaintCreate(BaseModel):
    """Schema for creating a complaint."""
    location: str
    description: str
    category: str | None = None
    image_url: str | None = None


class ComplaintVerify(BaseModel):
    """Schema for verifying/assigning complaint."""
    assigned_to: str | None = None


class ComplaintReject(BaseModel):
    """Schema for rejecting complaint."""
    reason: str


class ComplaintClose(BaseModel):
    """Schema for closing complaint."""
    resolution_notes: str | None = None


class ComplaintAssign(BaseModel):
    """Schema for assigning staff."""
    staff_name: str


class ComplaintOut(BaseModel):
    """Schema for complaint output."""
    id: int
    student_id: int
    student_type: str
    category: str
    priority: str
    location: str
    description: str
    image_url: str | None
    status: str
    assigned_to: str | None
    assigned_at: datetime | None
    resolution_notes: str | None
    rejection_reason: str | None
    created_at: datetime
    verified_at: datetime | None
    closed_at: datetime | None
    student_name: str | None = None
    
    class Config:
        from_attributes = True


# Student Endpoints

@router.post("", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    data: ComplaintCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Raise a new maintenance complaint. AI auto-categorizes and assesses priority."""
    if current_user.role not in [UserRole.STUDENT]:
        raise HTTPException(status_code=403, detail="Only students can raise complaints")
    
    if not data.location or len(data.location.strip()) < 3:
        raise HTTPException(status_code=400, detail="Location must be at least 3 characters")
    
    if not data.description or len(data.description.strip()) < 10:
        raise HTTPException(status_code=400, detail="Description must be at least 10 characters")
    
    service = ComplaintService(db)
    
    try:
        complaint = await service.create_complaint(
            student_id=current_user.id,
            student_type=current_user.student_category or "DAY_SCHOLAR",
            location=data.location.strip(),
            description=data.description.strip(),
            category=data.category,
            image_url=data.image_url
        )
        
        return _to_complaint_out(complaint)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my", response_model=list[ComplaintOut])
async def get_my_complaints(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get all complaints for the current student."""
    service = ComplaintService(db)
    complaints = await service.get_my_complaints(current_user.id)
    return [_to_complaint_out(c) for c in complaints]


# Admin Endpoints

@router.get("/pending", response_model=list[ComplaintOut])
async def get_pending_complaints(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Get pending complaints for admin (DAY_SCHOLAR only)."""
    service = ComplaintService(db)
    complaints = await service.get_pending_complaints(student_type="DAY_SCHOLAR")
    return [_to_complaint_out(c) for c in complaints]


@router.get("/admin/resolved", response_model=list[ComplaintOut])
async def get_admin_resolved_complaints(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Get resolved complaints for admin history."""
    service = ComplaintService(db)
    complaints = await service.get_resolved_complaints(student_type="DAY_SCHOLAR")
    return [_to_complaint_out(c) for c in complaints]


# Warden Endpoints

@router.get("/warden/pending", response_model=list[ComplaintOut])
async def get_warden_pending_complaints(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get pending complaints for warden (HOSTELLER only)."""
    if current_user.role != UserRole.WARDEN:
        raise HTTPException(status_code=403, detail="Only wardens can access this")
    
    service = ComplaintService(db)
    complaints = await service.get_pending_complaints(student_type="HOSTELLER")
    return [_to_complaint_out(c) for c in complaints]


@router.get("/warden/resolved", response_model=list[ComplaintOut])
async def get_warden_resolved_complaints(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get resolved complaints for warden history."""
    if current_user.role != UserRole.WARDEN:
        raise HTTPException(status_code=403, detail="Only wardens can access this")
    
    service = ComplaintService(db)
    complaints = await service.get_resolved_complaints(student_type="HOSTELLER")
    return [_to_complaint_out(c) for c in complaints]


# Action Endpoints

@router.post("/{complaint_id}/verify", response_model=ComplaintOut)
async def verify_complaint(
    complaint_id: int,
    data: ComplaintVerify,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Verify complaint and optionally assign to staff."""
    if current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Only admin or warden can verify")
    
    service = ComplaintService(db)
    try:
        complaint = await service.verify_complaint(complaint_id, current_user.id, data.assigned_to)
        return _to_complaint_out(complaint)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{complaint_id}/reject", response_model=ComplaintOut)
async def reject_complaint(
    complaint_id: int,
    data: ComplaintReject,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Reject complaint with reason."""
    if current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Only admin or warden can reject")
    
    if not data.reason or len(data.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="Rejection reason required")
    
    service = ComplaintService(db)
    try:
        complaint = await service.reject_complaint(complaint_id, current_user.id, data.reason.strip())
        return _to_complaint_out(complaint)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{complaint_id}/assign", response_model=ComplaintOut)
async def assign_staff(
    complaint_id: int,
    data: ComplaintAssign,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Assign complaint to maintenance staff."""
    if current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Only admin or warden can assign")
    
    service = ComplaintService(db)
    try:
        complaint = await service.assign_staff(complaint_id, current_user.id, data.staff_name)
        return _to_complaint_out(complaint)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{complaint_id}/close", response_model=ComplaintOut)
async def close_complaint(
    complaint_id: int,
    data: ComplaintClose,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Close complaint with resolution notes."""
    if current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Only admin or warden can close")
    
    service = ComplaintService(db)
    try:
        complaint = await service.close_complaint(complaint_id, current_user.id, data.resolution_notes)
        return _to_complaint_out(complaint)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class SuggestResolutionInput(BaseModel):
    """Schema for suggest resolution input."""
    description: str
    category: str
    assigned_to: str | None = None


class SuggestResolutionOutput(BaseModel):
    """Schema for suggest resolution output."""
    suggested_notes: str


@router.post("/{complaint_id}/suggest-resolution", response_model=SuggestResolutionOutput)
async def suggest_resolution_notes(
    complaint_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """AI-generated resolution notes suggestion."""
    if current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Only admin or warden can access")
    
    service = ComplaintService(db)
    complaint = await service.get_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    from app.services.ai_service import AIService
    suggested = await AIService.suggest_resolution_notes(
        description=complaint.description,
        category=complaint.category,
        assigned_to=complaint.assigned_to
    )
    
    return SuggestResolutionOutput(suggested_notes=suggested)


@router.get("/categories")
async def get_categories():
    """Get available complaint categories."""
    return [
        {"value": cat.value, "label": cat.value.title()}
        for cat in ComplaintCategory
    ]


@router.get("/priorities")
async def get_priorities():
    """Get priority levels."""
    return [
        {"value": pri.value, "label": pri.value.title()}
        for pri in ComplaintPriority
    ]


# Helper
def _to_complaint_out(c) -> ComplaintOut:
    """Convert Complaint model to output schema."""
    return ComplaintOut(
        id=c.id,
        student_id=c.student_id,
        student_type=c.student_type,
        category=c.category,
        priority=c.priority,
        location=c.location,
        description=c.description,
        image_url=c.image_url,
        status=c.status,
        assigned_to=c.assigned_to,
        assigned_at=c.assigned_at,
        resolution_notes=c.resolution_notes,
        rejection_reason=c.rejection_reason,
        created_at=c.created_at,
        verified_at=c.verified_at,
        closed_at=c.closed_at,
        student_name=f"{c.student.first_name} {c.student.last_name}" if c.student else None
    )
