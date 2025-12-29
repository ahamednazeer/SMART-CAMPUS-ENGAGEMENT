from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserRole, StudentCategory


class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole = UserRole.STUDENT
    student_category: StudentCategory | None = None
    register_number: str | None = None
    department: str | None = None
    batch: str | None = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str
    
    @field_validator('password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: UserRole | None = None
    student_category: StudentCategory | None = None
    register_number: str | None = None
    department: str | None = None
    batch: str | None = None
    is_active: bool | None = None


class UserOut(UserBase):
    """User output schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListOut(BaseModel):
    """List of users output schema."""
    users: list[UserOut]
    total: int


class BulkImportRequest(BaseModel):
    """Bulk user import request."""
    users: list[UserCreate]


class BulkImportResponse(BaseModel):
    """Bulk import response."""
    created: int
    failed: int
    errors: list[str]


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
