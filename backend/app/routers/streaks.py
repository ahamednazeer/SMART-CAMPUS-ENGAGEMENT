from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.streak_service import StreakService
from app.schemas.streak import (
    StreakOut, StreakDashboard, RecoveryRequestCreate, RecoveryRequestOut,
    RecoveryReview, StreakAnalytics
)

router = APIRouter(prefix="/streaks", tags=["Streaks"])


@router.get("/{pdf_id}", response_model=StreakOut)
async def get_streak(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user's streak for a PDF."""
    service = StreakService(db)
    return await service.get_student_streak(current_user.id, pdf_id)


@router.get("/{pdf_id}/dashboard", response_model=StreakDashboard)
async def get_streak_dashboard(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user's streak dashboard."""
    service = StreakService(db)
    return await service.get_student_dashboard(current_user, pdf_id)


@router.post("/recovery", response_model=RecoveryRequestOut, status_code=status.HTTP_201_CREATED)
async def request_recovery(
    data: RecoveryRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Submit a streak recovery request (hostellers only)."""
    service = StreakService(db)
    try:
        return await service.request_recovery(current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/admin/analytics", response_model=StreakAnalytics)
async def get_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get streak analytics (admin only)."""
    service = StreakService(db)
    return await service.get_analytics()


@router.get("/admin/recovery-requests", response_model=list[RecoveryRequestOut])
async def get_pending_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get pending recovery requests (admin only)."""
    service = StreakService(db)
    return await service.get_pending_requests()


@router.post("/admin/recovery-requests/{request_id}/review", response_model=RecoveryRequestOut)
async def review_request(
    request_id: int,
    data: RecoveryReview,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Review a recovery request (admin only)."""
    service = StreakService(db)
    try:
        return await service.review_recovery(request_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
