"""Router for Faculty Location & Availability module."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User, UserRole
from app.services.faculty_location_service import FacultyLocationService
from app.schemas.faculty_location import (
    CampusBuildingCreate, CampusBuildingUpdate, CampusBuildingOut,
    FacultyAvailabilityUpdate, FacultyLocationRefresh, FacultySettingsOut,
    FacultyLocationOut, FacultyLocationListOut,
    AdminFacultyListOut, FacultyLocationStats
)

router = APIRouter(prefix="/faculty-location", tags=["Faculty Location & Availability"])


# ============ Helper to require STAFF role ============

def require_staff(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require user to be STAFF (faculty)."""
    if current_user.role != UserRole.STAFF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only faculty/staff members can access this endpoint"
        )
    return current_user


# ============ Campus Buildings (Public read, Admin write) ============

@router.get("/buildings", response_model=list[CampusBuildingOut])
async def get_buildings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    include_inactive: bool = False
):
    """Get all campus buildings. Students and faculty can see active buildings."""
    service = FacultyLocationService(db)
    # Only admin can see inactive buildings
    if include_inactive and current_user.role != UserRole.ADMIN:
        include_inactive = False
    return await service.get_all_buildings(include_inactive)


@router.post("/admin/buildings", response_model=CampusBuildingOut)
async def create_building(
    data: CampusBuildingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Create a new campus building (admin only)."""
    service = FacultyLocationService(db)
    try:
        return await service.create_building(data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/admin/buildings/{building_id}", response_model=CampusBuildingOut)
async def update_building(
    building_id: int,
    data: CampusBuildingUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Update a campus building (admin only)."""
    service = FacultyLocationService(db)
    try:
        return await service.update_building(building_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/admin/buildings/{building_id}")
async def delete_building(
    building_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Soft delete a campus building (admin only)."""
    service = FacultyLocationService(db)
    success = await service.delete_building(building_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Building not found"
        )
    return {"message": "Building deleted successfully"}


# ============ Faculty Settings (STAFF only) ============

@router.get("/settings", response_model=FacultySettingsOut)
async def get_my_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)]
):
    """Get faculty's own availability settings."""
    service = FacultyLocationService(db)
    availability = await service.get_faculty_settings(current_user.id)
    
    return FacultySettingsOut(
        id=availability.id,
        faculty_id=availability.faculty_id,
        is_sharing_enabled=availability.is_sharing_enabled,
        availability_status=availability.availability_status,
        visibility_level=availability.visibility_level,
        status_message=availability.status_message,
        last_seen_building=CampusBuildingOut.model_validate(availability.last_seen_building) if availability.last_seen_building else None,
        last_seen_floor=availability.last_seen_floor,
        last_seen_at=availability.last_seen_at,
        updated_at=availability.updated_at
    )


@router.put("/settings", response_model=FacultySettingsOut)
async def update_my_settings(
    data: FacultyAvailabilityUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)]
):
    """Update faculty's own availability settings."""
    service = FacultyLocationService(db)
    availability = await service.update_faculty_settings(current_user.id, data)
    
    return FacultySettingsOut(
        id=availability.id,
        faculty_id=availability.faculty_id,
        is_sharing_enabled=availability.is_sharing_enabled,
        availability_status=availability.availability_status,
        visibility_level=availability.visibility_level,
        status_message=availability.status_message,
        last_seen_building=CampusBuildingOut.model_validate(availability.last_seen_building) if availability.last_seen_building else None,
        last_seen_floor=availability.last_seen_floor,
        last_seen_at=availability.last_seen_at,
        updated_at=availability.updated_at
    )


@router.post("/refresh", response_model=FacultySettingsOut)
async def refresh_my_location(
    data: FacultyLocationRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_staff)]
):
    """Manually refresh faculty's last-seen location."""
    service = FacultyLocationService(db)
    try:
        availability = await service.refresh_location(current_user.id, data)
        
        return FacultySettingsOut(
            id=availability.id,
            faculty_id=availability.faculty_id,
            is_sharing_enabled=availability.is_sharing_enabled,
            availability_status=availability.availability_status,
            visibility_level=availability.visibility_level,
            status_message=availability.status_message,
            last_seen_building=CampusBuildingOut.model_validate(availability.last_seen_building) if availability.last_seen_building else None,
            last_seen_floor=availability.last_seen_floor,
            last_seen_at=availability.last_seen_at,
            updated_at=availability.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============ Student View (STUDENT only) ============

@router.get("/faculty", response_model=FacultyLocationListOut)
async def get_available_faculty(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    search: str | None = Query(None, description="Search by name or department"),
    department: str | None = Query(None, description="Filter by department"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get list of available faculty for students. Respects visibility settings."""
    if current_user.role not in [UserRole.STUDENT, UserRole.HOSTELLER, UserRole.DAY_SCHOLAR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    service = FacultyLocationService(db)
    faculty_list, total = await service.get_available_faculty(
        viewer_department=current_user.department,
        is_admin=False,
        search_query=search,
        department_filter=department,
        page=page,
        page_size=page_size
    )
    
    return FacultyLocationListOut(
        faculty=faculty_list,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/faculty/{faculty_id}", response_model=FacultyLocationOut)
async def get_faculty_by_id(
    faculty_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get specific faculty info for students. Respects visibility settings."""
    if current_user.role not in [UserRole.STUDENT, UserRole.HOSTELLER, UserRole.DAY_SCHOLAR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    service = FacultyLocationService(db)
    faculty = await service.get_faculty_by_id(
        faculty_id,
        viewer_department=current_user.department,
        is_admin=False
    )
    
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found or not visible"
        )
    
    return faculty


@router.get("/departments", response_model=list[str])
async def get_faculty_departments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get list of departments that have faculty (for filtering)."""
    service = FacultyLocationService(db)
    return await service.get_faculty_departments()


# ============ Admin Endpoints ============

@router.get("/admin/all", response_model=AdminFacultyListOut)
async def get_all_faculty_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Get all faculty with their settings (admin only)."""
    service = FacultyLocationService(db)
    faculty_list = await service.get_all_faculty_for_admin()
    
    return AdminFacultyListOut(
        faculty=faculty_list,
        total=len(faculty_list)
    )


@router.get("/admin/stats", response_model=FacultyLocationStats)
async def get_faculty_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Get faculty location module statistics (admin only)."""
    service = FacultyLocationService(db)
    stats = await service.get_faculty_stats()
    return FacultyLocationStats(**stats)
