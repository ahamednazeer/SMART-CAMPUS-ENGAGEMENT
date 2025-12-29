"""API router for warden operations (Outpass approval, hostel oversight)."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import require_warden
from app.models.user import User, UserRole
from app.models.outpass import OutpassStatus
from app.services.outpass_service import OutpassService
from app.services.hostel_service import HostelService
from app.schemas.outpass import OutpassOut, OutpassWithStudentDetails
from app.schemas.hostel import HostelWithDetails, HostelAssignmentWithDetails


router = APIRouter(prefix="/warden", tags=["Warden"])


# ==================== HOSTEL INFO ====================

@router.get("/hostel", response_model=HostelWithDetails | None)
async def get_my_hostel(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Get the hostel managed by the current warden."""
    service = HostelService(db)
    hostel = await service.get_warden_hostel(current_user.id)
    
    if not hostel:
        return None
    
    # Get details
    hostels = await service.list_hostels()
    for h in hostels:
        if h.id == hostel.id:
            return h
    
    return None


@router.get("/students", response_model=list[HostelAssignmentWithDetails])
async def get_hostel_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Get all students in the warden's hostel."""
    hostel_service = HostelService(db)
    hostel = await hostel_service.get_warden_hostel(current_user.id)
    
    if not hostel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not assigned as warden to any hostel"
        )
    
    return await hostel_service.get_hostel_students(hostel.id)


# ==================== OUTPASS MANAGEMENT ====================

@router.get("/outpass/pending", response_model=list[OutpassWithStudentDetails])
async def get_pending_outpasses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get pending outpass requests for approval."""
    service = OutpassService(db)
    try:
        outpasses, total = await service.get_pending_for_warden(
            current_user.id, page, page_size
        )
        return outpasses
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/outpass/all", response_model=list[OutpassWithStudentDetails])
async def get_all_outpasses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)],
    status_filter: OutpassStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get all outpass requests for the hostel."""
    service = OutpassService(db)
    try:
        outpasses, total = await service.get_all_hostel_outpasses(
            current_user.id, status_filter, page, page_size
        )
        return outpasses
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/outpass/student/{student_id}", response_model=list[OutpassOut])
async def get_student_outpass_history(
    student_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Get outpass history for a specific student."""
    service = OutpassService(db)
    try:
        return await service.get_outpass_history_for_student(current_user.id, student_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


class ApproveRejectRequest(BaseModel):
    """Request body for approval/rejection."""
    rejection_reason: str | None = None


@router.post("/outpass/{outpass_id}/approve", response_model=OutpassOut)
async def approve_outpass(
    outpass_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Approve an outpass request."""
    service = OutpassService(db)
    try:
        outpass = await service.approve_outpass(outpass_id, current_user.id)
        return OutpassOut.model_validate(outpass)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/outpass/{outpass_id}/reject", response_model=OutpassOut)
async def reject_outpass(
    outpass_id: int,
    body: ApproveRejectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_warden)]
):
    """Reject an outpass request."""
    if not body.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required"
        )
    
    service = OutpassService(db)
    try:
        outpass = await service.reject_outpass(
            outpass_id, current_user.id, body.rejection_reason
        )
        return OutpassOut.model_validate(outpass)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
