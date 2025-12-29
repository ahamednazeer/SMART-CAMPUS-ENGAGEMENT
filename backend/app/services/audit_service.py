from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository
from app.models.audit_log import AuditLog

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuditRepository(db)

    async def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        return await self.repo.create(log)

    async def get_logs(self, skip: int = 0, limit: int = 100) -> list[AuditLog]:
        """Get all audit logs (admin only)."""
        return await self.repo.get_all(skip, limit)

    async def get_user_logs(self, user_id: int, skip: int = 0, limit: int = 100) -> list[AuditLog]:
        """Get logs for a specific user."""
        return await self.repo.get_by_user(user_id, skip, limit)
