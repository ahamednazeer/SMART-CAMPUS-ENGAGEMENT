"""
Attendance API routes for students.
"""
from typing import Annotated
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_student
from app.models.user import User
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import (
    ProfilePhotoOut,
    AttendancePreCheckOut,
    AttendanceMarkResult,
    AttendanceRecordOut,
    AttendanceRecordListOut,
    AttendanceAttemptOut,
    AttendanceAttemptListOut,
    LocationData,
    StudentAttendanceStatsOut
)


router = APIRouter(prefix="/attendance", tags=["Attendance"])


# ============== Profile Photo Endpoints ==============

@router.post("/profile-photo", response_model=ProfilePhotoOut)
async def upload_profile_photo(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Upload a profile photo for face recognition reference."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    service = AttendanceService(db)
    try:
        return await service.upload_profile_photo(current_user, file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/profile-photo/status", response_model=ProfilePhotoOut | None)
async def get_profile_photo_status(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get the current profile photo status."""
    service = AttendanceService(db)
    return await service.get_profile_photo_status(current_user.id)


# ============== Attendance Pre-Check ==============

@router.get("/pre-check", response_model=AttendancePreCheckOut)
async def pre_check_attendance(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Check if student can mark attendance (prerequisites check)."""
    service = AttendanceService(db)
    return await service.check_attendance_prerequisites(current_user)


# ============== Mark Attendance ==============

@router.post("/mark", response_model=AttendanceMarkResult)
async def mark_attendance(
    file: Annotated[UploadFile, File(description="Live captured face image")],
    latitude: Annotated[float, Form()],
    longitude: Annotated[float, Form()],
    accuracy: Annotated[float, Form()],
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Mark attendance with location and face verification.
    
    Requires:
    - GPS location (latitude, longitude, accuracy)
    - Live captured face image (not from gallery)
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create location data object
    location = LocationData(
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy
    )
    
    service = AttendanceService(db)
    
    # First do pre-check
    pre_check = await service.check_attendance_prerequisites(current_user)
    if not pre_check.can_mark:
        blockers_text = ", ".join(pre_check.blockers)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark attendance: {blockers_text}"
        )
    
    # Mark attendance
    return await service.mark_attendance(current_user, location, file)


# ============== Attendance Status & History ==============

@router.get("/today", response_model=AttendanceRecordOut | None)
async def get_today_attendance(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get today's attendance status."""
    service = AttendanceService(db)
    return await service.get_today_status(current_user.id)


@router.get("/history", response_model=AttendanceRecordListOut)
async def get_attendance_history(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None
):
    """Get attendance history for the current student."""
    service = AttendanceService(db)
    records = await service.get_student_attendance_history(
        current_user.id, start_date, end_date
    )
    return AttendanceRecordListOut(records=records, total=len(records))


@router.get("/attempts", response_model=AttendanceAttemptListOut)
async def get_attendance_attempts(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get attendance attempt history (including failures)."""
    service = AttendanceService(db)
    attempts = await service.get_student_attempts(current_user.id)
    return AttendanceAttemptListOut(attempts=attempts, total=len(attempts))


@router.get("/stats", response_model=StudentAttendanceStatsOut)
async def get_attendance_stats(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None
):
    """Get attendance statistics for the current student."""
    service = AttendanceService(db)
    return await service.get_my_attendance_stats(current_user, start_date, end_date)
