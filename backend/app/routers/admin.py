from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.streak_service import StreakService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Admin"])


class SystemStats(BaseModel):
    """System statistics."""
    users: dict
    streaks: dict

class AuditLogOut(BaseModel):
    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: int | None
    details: dict | None
    ip_address: str | None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get system statistics (admin only)."""
    user_repo = UserRepository(db)
    streak_service = StreakService(db)
    
    total_users = await user_repo.count()
    users_by_role = await user_repo.count_by_role()
    streak_analytics = await streak_service.get_analytics()
    
    return SystemStats(
        users={
            "total": total_users,
            "byRole": users_by_role,
        },
        streaks={
            "active": streak_analytics.active_streaks,
            "broken": streak_analytics.broken_streaks,
            "avgLength": streak_analytics.avg_streak_length,
            "pendingRecovery": streak_analytics.pending_recovery_requests,
        }
    )

@router.get("/audit-logs", response_model=list[AuditLogOut])
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100
):
    """Get system audit logs (admin only)."""
    service = AuditService(db)
    return await service.get_logs(skip, limit)
