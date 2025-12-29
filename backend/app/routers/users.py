from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut, UserListOut,
    BulkImportRequest, BulkImportResponse, PasswordChange
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListOut)
async def get_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100
):
    """Get all users (admin only)."""
    service = UserService(db)
    return await service.get_all_users(skip, limit)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Create a new user (admin only)."""
    service = UserService(db)
    audit = AuditService(db)
    try:
        user = await service.create_user(data)
        await audit.log_action(
            user_id=admin.id,
            action="CREATE",
            resource_type="user",
            resource_id=user.id,
            details={"username": user.username, "email": user.email, "role": user.role}
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserOut)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user's profile."""
    return UserOut.model_validate(current_user)


@router.put("/me", response_model=UserOut)
async def update_my_profile(
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Update current user's profile."""
    service = UserService(db)
    # Only allow updating certain fields for self
    allowed_data = UserUpdate(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    try:
        return await service.update_user(current_user.id, allowed_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChange,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Change current user's password."""
    service = UserService(db)
    try:
        await service.change_password(current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get user by ID (admin only)."""
    service = UserService(db)
    try:
        return await service.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Update a user (admin only)."""
    service = UserService(db)
    try:
        return await service.update_user(user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Delete a user (admin only)."""
    service = UserService(db)
    audit = AuditService(db)
    try:
        await service.delete_user(user_id)
        await audit.log_action(
            user_id=admin.id,
            action="DELETE",
            resource_type="user",
            resource_id=user_id,
            details={"deleted_user_id": user_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/bulk-import", response_model=BulkImportResponse)
async def bulk_import_users(
    data: BulkImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Bulk import users (admin only)."""
    service = UserService(db)
    return await service.bulk_import(data)
