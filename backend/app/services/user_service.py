from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut, UserListOut,
    BulkImportRequest, BulkImportResponse, PasswordChange
)


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def create_user(self, data: UserCreate) -> UserOut:
        """Create a new user."""
        # Check for existing username
        existing = await self.user_repo.get_by_username(data.username)
        if existing:
            raise ValueError("Username already exists")
        
        # Check for existing email
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValueError("Email already exists")
        
        # Check for existing register number
        if data.register_number:
            existing = await self.user_repo.get_by_register_number(data.register_number)
            if existing:
                raise ValueError("Register number already exists")
        
        # Create user
        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            student_category=data.student_category,
            register_number=data.register_number,
            department=data.department,
            batch=data.batch,
        )
        
        user = await self.user_repo.create(user)
        return UserOut.model_validate(user)
    
    async def get_user(self, user_id: int) -> UserOut:
        """Get user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return UserOut.model_validate(user)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> UserListOut:
        """Get all users with pagination."""
        users = await self.user_repo.get_all(skip, limit)
        total = await self.user_repo.count()
        return UserListOut(
            users=[UserOut.model_validate(u) for u in users],
            total=total
        )
    
    async def update_user(self, user_id: int, data: UserUpdate) -> UserOut:
        """Update an existing user."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        
        # Check uniqueness of email if changed
        if data.email and data.email != user.email:
            existing = await self.user_repo.get_by_email(data.email)
            if existing:
                raise ValueError("Email already exists")
        
        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        user = await self.user_repo.update(user)
        return UserOut.model_validate(user)
    
    async def delete_user(self, user_id: int) -> None:
        """Delete a user."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
            
        # Manually cascade delete related records to avoid IntegrityError (NotNullViolation)
        # because defaults in SQLAlchemy relationships might try to set FK=Null
        from sqlalchemy import delete
        from app.models.attendance import AttendanceAttempt, AttendanceRecord, ProfilePhoto
        from app.models.reading import DailyReadingLog, ReadingSession
        from app.models.quiz import QuizAttempt
        
        # Delete attendance data
        await self.db.execute(delete(AttendanceAttempt).where(AttendanceAttempt.student_id == user_id))
        await self.db.execute(delete(AttendanceRecord).where(AttendanceRecord.student_id == user_id))
        await self.db.execute(delete(ProfilePhoto).where(ProfilePhoto.student_id == user_id))
        
        # Delete reading/quiz data if any
        # (Note: simpler to just delete user if DB cascade is set, but this ensures safety against SQLAlchemy's SET NULL behavior)
        await self.db.execute(delete(ReadingSession).where(ReadingSession.student_id == user_id))
        await self.db.execute(delete(DailyReadingLog).where(DailyReadingLog.student_id == user_id))
        await self.db.execute(delete(QuizAttempt).where(QuizAttempt.student_id == user_id))
        
        # Finally delete user
        await self.user_repo.delete(user)
    
    async def change_password(self, user: User, data: PasswordChange) -> None:
        """Change user password."""
        if not verify_password(data.current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        user.password_hash = hash_password(data.new_password)
        await self.user_repo.update(user)
    
    async def bulk_import(self, data: BulkImportRequest) -> BulkImportResponse:
        """Bulk import users."""
        created = 0
        failed = 0
        errors = []
        
        for user_data in data.users:
            try:
                await self.create_user(user_data)
                created += 1
            except ValueError as e:
                failed += 1
                errors.append(f"{user_data.username}: {str(e)}")
        
        return BulkImportResponse(created=created, failed=failed, errors=errors)
    
    async def get_students_by_batch(self, batch: str) -> list[UserOut]:
        """Get all students in a batch."""
        users = await self.user_repo.get_students_by_batch(batch)
        return [UserOut.model_validate(u) for u in users]
