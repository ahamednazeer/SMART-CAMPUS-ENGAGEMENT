from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole


class UserRepository:
    """Repository for user data access operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_register_number(self, register_number: str) -> User | None:
        """Get user by register number."""
        result = await self.db.execute(
            select(User).where(User.register_number == register_number)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination."""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_role(self, role: UserRole) -> list[User]:
        """Get all users with a specific role."""
        result = await self.db.execute(
            select(User).where(User.role == role).order_by(User.last_name)
        )
        return list(result.scalars().all())
    
    async def get_students_by_batch(self, batch: str) -> list[User]:
        """Get all students in a batch."""
        result = await self.db.execute(
            select(User).where(
                User.batch == batch,
                User.role.in_([UserRole.STUDENT, UserRole.HOSTELLER, UserRole.DAY_SCHOLAR])
            ).order_by(User.last_name)
        )
        return list(result.scalars().all())
    
    async def count(self) -> int:
        """Count total users."""
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar() or 0
    
    async def count_by_role(self) -> dict[str, int]:
        """Count users by role."""
        result = await self.db.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        return {str(row[0].value): row[1] for row in result.all()}
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user: User) -> None:
        """Delete a user."""
        await self.db.delete(user)
        await self.db.flush()
