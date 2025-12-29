"""API router for student outpass requests."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_hosteller
from app.models.user import User, StudentCategory
from app.models.outpass import OutpassStatus
from app.services.outpass_service import OutpassService
from app.services.hostel_service import HostelService
from app.schemas.outpass import OutpassCreate, OutpassOut, OutpassSummary, OutpassListOut
from app.schemas.hostel import StudentHostelInfo


router = APIRouter(prefix="/outpass", tags=["Outpass"])


# ==================== HOSTEL INFO ====================

@router.get("/hostel-info", response_model=StudentHostelInfo)
async def get_hostel_info(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current student's hostel assignment info."""
    if current_user.student_category != StudentCategory.HOSTELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hostellers can access hostel services"
        )
    
    service = HostelService(db)
    return await service.get_student_hostel_info(current_user.id)


# ==================== OUTPASS REQUESTS ====================

@router.post("", response_model=OutpassOut, status_code=status.HTTP_201_CREATED)
async def create_outpass(
    data: OutpassCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Submit a new outpass request."""
    # Check if student is hosteller
    if current_user.student_category != StudentCategory.HOSTELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hostellers can apply for outpass"
        )
    
    service = OutpassService(db)
    try:
        outpass = await service.submit_outpass(current_user.id, data)
        return OutpassOut.model_validate(outpass)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("", response_model=OutpassListOut)
async def list_outpasses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: OutpassStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get current student's outpass history."""
    if current_user.student_category != StudentCategory.HOSTELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hostellers can access outpass services"
        )
    
    service = OutpassService(db)
    outpasses, total = await service.get_student_outpasses(
        current_user.id, status_filter, page, page_size
    )
    return OutpassListOut(
        outpasses=outpasses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/summary", response_model=OutpassSummary)
async def get_outpass_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get summary of student's outpass usage."""
    if current_user.student_category != StudentCategory.HOSTELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hostellers can access outpass services"
        )
    
    service = OutpassService(db)
    return await service.get_student_summary(current_user.id)


@router.get("/{outpass_id}", response_model=OutpassOut)
async def get_outpass(
    outpass_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get details of a specific outpass request."""
    if current_user.student_category != StudentCategory.HOSTELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hostellers can access outpass services"
        )
    
    service = OutpassService(db)
    try:
        return await service.get_outpass_details(outpass_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
