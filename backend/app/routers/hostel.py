"""API router for hostel management (Admin operations)."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.services.hostel_service import HostelService
from app.schemas.hostel import (
    HostelCreate, HostelUpdate, HostelOut, HostelWithDetails,
    HostelRoomCreate, HostelRoomUpdate, HostelRoomOut, HostelRoomWithOccupancy,
    HostelAssignmentCreate, HostelAssignmentOut, HostelAssignmentWithDetails
)


router = APIRouter(prefix="/admin/hostels", tags=["Hostel Management"])


# ==================== HOSTEL CRUD ====================

@router.post("", response_model=HostelOut, status_code=status.HTTP_201_CREATED)
async def create_hostel(
    data: HostelCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Create a new hostel (Admin only)."""
    service = HostelService(db)
    try:
        return await service.create_hostel(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[HostelWithDetails])
async def list_hostels(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    include_inactive: bool = False
):
    """List all hostels with details (Admin only)."""
    service = HostelService(db)
    return await service.list_hostels(include_inactive)


@router.get("/{hostel_id}", response_model=HostelOut)
async def get_hostel(
    hostel_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get hostel by ID (Admin only)."""
    service = HostelService(db)
    hostel = await service.get_hostel(hostel_id)
    if not hostel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hostel not found")
    return hostel


@router.put("/{hostel_id}", response_model=HostelOut)
async def update_hostel(
    hostel_id: int,
    data: HostelUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Update hostel (Admin only)."""
    service = HostelService(db)
    try:
        return await service.update_hostel(hostel_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{hostel_id}/assign-warden")
async def assign_warden(
    hostel_id: int,
    warden_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Assign warden to hostel (Admin only)."""
    service = HostelService(db)
    try:
        hostel = await service.assign_warden(hostel_id, warden_id)
        return {"message": "Warden assigned successfully", "hostel_id": hostel.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{hostel_id}/remove-warden")
async def remove_warden(
    hostel_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Remove warden from hostel (Admin only)."""
    service = HostelService(db)
    try:
        await service.remove_warden(hostel_id)
        return {"message": "Warden removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== ROOM CRUD ====================

@router.post("/{hostel_id}/rooms", response_model=HostelRoomOut, status_code=status.HTTP_201_CREATED)
async def add_room(
    hostel_id: int,
    data: HostelRoomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Add room to hostel (Admin only)."""
    if data.hostel_id != hostel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hostel ID in path and body must match"
        )
    service = HostelService(db)
    try:
        return await service.add_room(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{hostel_id}/rooms", response_model=list[HostelRoomWithOccupancy])
async def get_hostel_rooms(
    hostel_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    include_inactive: bool = False
):
    """Get all rooms in a hostel (Admin only)."""
    service = HostelService(db)
    return await service.get_hostel_rooms(hostel_id, include_inactive)


@router.put("/rooms/{room_id}", response_model=HostelRoomOut)
async def update_room(
    room_id: int,
    data: HostelRoomUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Update room (Admin only)."""
    service = HostelService(db)
    try:
        return await service.update_room(room_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== STUDENT ASSIGNMENTS ====================

@router.post("/assignments", response_model=HostelAssignmentOut, status_code=status.HTTP_201_CREATED)
async def assign_student(
    data: HostelAssignmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Assign student to a room (Admin only)."""
    service = HostelService(db)
    try:
        return await service.assign_student(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/assignments/{student_id}")
async def remove_student_assignment(
    student_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Remove student's hostel assignment (Admin only)."""
    service = HostelService(db)
    removed = await service.remove_student_assignment(student_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active assignment found for student"
        )
    return {"message": "Assignment removed successfully"}


@router.get("/{hostel_id}/students", response_model=list[HostelAssignmentWithDetails])
async def get_hostel_students(
    hostel_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get all students in a hostel (Admin only)."""
    service = HostelService(db)
    return await service.get_hostel_students(hostel_id)
