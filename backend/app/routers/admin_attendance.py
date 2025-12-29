"""
Admin attendance management API routes.
"""
from typing import Annotated
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import (
    ProfilePhotoOut, ProfilePhotoListOut, ProfilePhotoApproval,
    GeofenceCreate, GeofenceUpdate, GeofenceOut, GeofenceListOut,
    AttendanceWindowCreate, AttendanceWindowUpdate, AttendanceWindowOut, AttendanceWindowListOut,
    AttendanceRecordOut, AttendanceRecordListOut,
    AttendanceAttemptOut, AttendanceAttemptListOut,
    AttendanceDashboardStats,
    DetailedAttendanceListOut,
    HolidayCreate, HolidayOut, HolidayListOut, BulkHolidayCreate,
    AcademicYearSettingsUpdate, AcademicYearSettingsOut
)


router = APIRouter(prefix="/admin/attendance", tags=["Admin - Attendance"])


# ============== Profile Photo Management ==============

@router.get("/profile-photos/pending", response_model=ProfilePhotoListOut)
async def get_pending_photos(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50
):
    """Get all pending profile photos for review."""
    service = AttendanceService(db)
    photos, total = await service.get_pending_photos(skip, limit)
    return ProfilePhotoListOut(photos=photos, total=total)


@router.post("/profile-photos/{photo_id}/review", response_model=ProfilePhotoOut)
async def review_profile_photo(
    photo_id: int,
    approval: ProfilePhotoApproval,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Approve or reject a profile photo."""
    service = AttendanceService(db)
    try:
        return await service.review_profile_photo(photo_id, current_user, approval)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== Geofence Management ==============

@router.post("/geofences", response_model=GeofenceOut)
async def create_geofence(
    data: GeofenceCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new campus geofence."""
    service = AttendanceService(db)
    return await service.create_geofence(data, current_user)


@router.get("/geofences", response_model=GeofenceListOut)
async def get_geofences(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get all geofences."""
    service = AttendanceService(db)
    geofences = await service.get_geofences()
    return GeofenceListOut(geofences=geofences, total=len(geofences))


@router.put("/geofences/{geofence_id}", response_model=GeofenceOut)
async def update_geofence(
    geofence_id: int,
    data: GeofenceUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update a geofence."""
    service = AttendanceService(db)
    try:
        return await service.update_geofence(geofence_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/geofences/{geofence_id}")
async def delete_geofence(
    geofence_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete a geofence."""
    service = AttendanceService(db)
    try:
        await service.delete_geofence(geofence_id)
        return {"message": "Geofence deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== Attendance Window Management ==============

@router.post("/windows", response_model=AttendanceWindowOut)
async def create_attendance_window(
    data: AttendanceWindowCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new attendance time window."""
    service = AttendanceService(db)
    return await service.create_attendance_window(data)


@router.get("/windows", response_model=AttendanceWindowListOut)
async def get_attendance_windows(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get all attendance windows."""
    service = AttendanceService(db)
    windows = await service.get_attendance_windows()
    return AttendanceWindowListOut(windows=windows, total=len(windows))


@router.delete("/windows/{window_id}")
async def delete_attendance_window(
    window_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete an attendance window."""
    service = AttendanceService(db)
    try:
        await service.delete_attendance_window(window_id)
        return {"message": "Attendance window deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== Dashboard & Reports ==============

@router.get("/dashboard", response_model=AttendanceDashboardStats)
async def get_dashboard_stats(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    target_date: date | None = None
):
    """Get attendance dashboard statistics."""
    if target_date is None:
        target_date = date.today()
    
    service = AttendanceService(db)
    return await service.get_dashboard_stats(target_date)


@router.get("/detailed", response_model=DetailedAttendanceListOut)
async def get_detailed_attendance(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    target_date: date | None = None
):
    """Get detailed student-by-student attendance for a date."""
    if target_date is None:
        target_date = date.today()
    
    service = AttendanceService(db)
    return await service.get_detailed_attendance_for_date(target_date)


@router.get("/records", response_model=AttendanceRecordListOut)
async def get_attendance_records(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    target_date: date | None = None
):
    """Get all attendance records for a date."""
    if target_date is None:
        target_date = date.today()
    
    service = AttendanceService(db)
    records = await service.get_all_records_for_date(target_date)
    return AttendanceRecordListOut(records=records, total=len(records))


@router.get("/failed-attempts", response_model=AttendanceAttemptListOut)
async def get_failed_attempts(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """Get all failed attendance attempts for audit."""
    service = AttendanceService(db)
    attempts = await service.get_failed_attempts(start_date, end_date)
    return AttendanceAttemptListOut(attempts=attempts, total=len(attempts))


# ============== Holiday Calendar Management ==============

@router.post("/holidays", response_model=HolidayOut)
async def create_holiday(
    holiday_data: HolidayCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new holiday/non-working day."""
    service = AttendanceService(db)
    try:
        return await service.create_holiday(current_user.id, holiday_data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/holidays", response_model=HolidayListOut)
async def get_holidays(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None
):
    """Get all holidays, optionally filtered by date range."""
    service = AttendanceService(db)
    return await service.get_holidays(start_date, end_date)


@router.delete("/holidays/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete a holiday."""
    service = AttendanceService(db)
    success = await service.delete_holiday(holiday_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return {"success": True, "message": "Holiday deleted"}


@router.post("/holidays/bulk")
async def bulk_create_holidays(
    data: BulkHolidayCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Bulk create holidays from pasted text."""
    service = AttendanceService(db)
    result = await service.bulk_create_holidays(current_user.id, data.text, data.year)
    return result


# ============== Academic Year Settings ==============

@router.get("/settings/academic-year", response_model=AcademicYearSettingsOut)
async def get_academic_year_settings(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get the configured academic year start and end dates."""
    service = AttendanceService(db)
    return await service.get_academic_year_settings()


@router.put("/settings/academic-year", response_model=AcademicYearSettingsOut)
async def update_academic_year_settings(
    settings: AcademicYearSettingsUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update the academic year start and end dates."""
    service = AttendanceService(db)
    try:
        return await service.update_academic_year_settings(
            current_user.id,
            settings.start_date,
            settings.end_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
